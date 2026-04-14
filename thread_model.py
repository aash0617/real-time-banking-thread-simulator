import time
from concurrent.futures import ThreadPoolExecutor, as_completed
 
 
# ─────────────────────────────────────────────────────────────
#  THREAD MAPPING MODELS
#  Demonstrates how user-level threads map to kernel threads.
#
#  All three models run the same set of TransactionThreads —
#  the difference is HOW they are executed and with what level
#  of parallelism.
# ─────────────────────────────────────────────────────────────


def _expected_balance(start_balance, transaction_data):
    """Compute the deterministic final balance for the given transactions."""
    balance = start_balance
    for txn_type, amount in transaction_data:
        if txn_type == "deposit":
            balance += amount
        elif txn_type == "withdraw" and balance >= amount:
            balance -= amount
    return balance


def _build_summary_row(name, elapsed, final_balance, expected_balance, start_balance):
    balance_error = final_balance - expected_balance
    return {
        "model": name,
        "time": elapsed,
        "final_balance": final_balance,
        "expected_balance": expected_balance,
        "balance_error": balance_error,
        "correct": balance_error == 0,
        "throughput_per_sec": 0.0,
    }
 
 
class ManyToOneModel:
    """
    MANY-TO-ONE MODEL
    -----------------
    All user threads map to a SINGLE kernel thread (worker).
    Only one transaction executes at a time — no parallelism.
    
    Real-world analogy: One bank teller serving all customers
    one by one, no matter how many are waiting.
    
    Pros : Simple, no race conditions even without locks
    Cons : Slow — all transactions are sequential
    """
 
    def __init__(self):
        self.model_name = "Many-to-One"
        self.results = []
 
    def run_transactions(self, transactions):
        """
        Uses a thread pool with max_workers=1.
        All transactions are submitted but only one runs at a time.
        """
        print(f"\n{'='*50}")
        print(f"  MODEL: {self.model_name}")
        print(f"  Workers: 1  |  Transactions: {len(transactions)}")
        print(f"{'='*50}")
 
        start_time = time.perf_counter()
 
        with ThreadPoolExecutor(max_workers=1) as executor:
            # Submit all transaction run() methods to the single worker
            futures = {executor.submit(t.run): t for t in transactions}
 
            for future in as_completed(futures):
                t = futures[future]
                try:
                    future.result()
                    print(f"  [DONE] Thread {t.thread_id} | {t.txn_type} ₹{t.amount}")
                except Exception as e:
                    print(f"  [ERROR] Thread {t.thread_id}: {e}")
 
        elapsed = time.perf_counter() - start_time
        print(f"\n  Total time: {elapsed:.2f}s  |  Context: Sequential (1 worker)")
        return elapsed
 
 
class OneToOneModel:
    """
    ONE-TO-ONE MODEL
    ----------------
    Each user thread maps directly to one kernel thread.
    This is what Python's threading.Thread does by default.
    All transactions can run truly in parallel (on separate CPU cores).
    
    Real-world analogy: Each customer gets their own dedicated teller.
    
    Pros : True parallelism — fastest for independent tasks
    Cons : High memory overhead for large numbers of threads
    """
 
    def __init__(self):
        self.model_name = "One-to-One"
        self.results = []
 
    def run_transactions(self, transactions):
        """
        Starts each TransactionThread directly using thread.start().
        Each maps to its own OS-level thread.
        """
        print(f"\n{'='*50}")
        print(f"  MODEL: {self.model_name}")
        print(f"  Workers: {len(transactions)} (one per transaction)")
        print(f"  Transactions: {len(transactions)}")
        print(f"{'='*50}")
 
        start_time = time.perf_counter()
 
        # Start all threads simultaneously
        for t in transactions:
            t.start()
            print(f"  [STARTED] Thread {t.thread_id} | {t.txn_type} ₹{t.amount}")
 
        # Wait for all to complete
        for t in transactions:
            t.join()
            print(f"  [DONE]    Thread {t.thread_id} | {t.txn_type} ₹{t.amount}")
 
        elapsed = time.perf_counter() - start_time
        print(f"\n  Total time: {elapsed:.2f}s  |  Context: Parallel ({len(transactions)} workers)")
        return elapsed
 
 
class ManyToManyModel:
    """
    MANY-TO-MANY MODEL
    ------------------
    N user threads are multiplexed over M kernel threads, where M <= N.
    The pool manages which thread gets CPU time.
    
    Real-world analogy: 10 customers served by 3 tellers.
    When a teller finishes, they call the next customer.
    
    Pros : Balanced — good parallelism without thread explosion
    Cons : Slightly more complex coordination
    
    This is the most realistic model for production banking systems.
    """
 
    def __init__(self, num_workers=3):
        self.model_name = "Many-to-Many"
        self.num_workers = num_workers
        self.results = []
 
    def run_transactions(self, transactions):
        """
        Uses a thread pool with num_workers workers to handle
        all transactions. Worker threads are reused across jobs.
        """
        print(f"\n{'='*50}")
        print(f"  MODEL: {self.model_name}")
        print(f"  Workers: {self.num_workers}  |  Transactions: {len(transactions)}")
        print(f"{'='*50}")
 
        start_time = time.perf_counter()
 
        with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            futures = {executor.submit(t.run): t for t in transactions}
 
            for future in as_completed(futures):
                t = futures[future]
                try:
                    future.result()
                    print(f"  [DONE] Thread {t.thread_id} | {t.txn_type} ₹{t.amount}")
                except Exception as e:
                    print(f"  [ERROR] Thread {t.thread_id}: {e}")
 
        elapsed = time.perf_counter() - start_time
        print(f"\n  Total time: {elapsed:.2f}s  |  Context: {self.num_workers} workers pooled")
        return elapsed
 
 
# ─────────────────────────────────────────────────────────────
#  COMPARISON RUNNER
#  Run all 3 models with the same transactions and compare times.
# ─────────────────────────────────────────────────────────────
 
def compare_models(account_class, transaction_data):
    """
    Runs the same set of transactions under all three models
    and prints a side-by-side performance comparison.

    Note: this module is about concurrency, so ML metrics such as
    train/test accuracy, MSE, MAE, overfitting, and underfitting do
    not apply here. The useful checks are correctness of the final
    balance, runtime, and relative speedup.
 
    Args:
        account_class : The BankAccount class to instantiate
        transaction_data : List of (txn_type, amount) tuples
    """
    from transaction_thread import TransactionThread
 
    if not transaction_data:
        raise ValueError("transaction_data must contain at least one transaction")

    results = {}
    start_balance = 1000
    expected_balance = _expected_balance(start_balance, transaction_data)
 
    models = [
        ("Many-to-One",  ManyToOneModel()),
        ("One-to-One",   OneToOneModel()),
        ("Many-to-Many", ManyToManyModel(num_workers=3)),
    ]

    baseline_time = None
 
    for name, model in models:
        # Fresh account for each model so balances don't mix
        account = account_class("COMPARE", start_balance)
 
        # Rebuild threads (can't reuse — threads can only start once)
        threads = [
            TransactionThread(i + 1, account, txn_type, amount, processing_time=1)
            for i, (txn_type, amount) in enumerate(transaction_data)
        ]
 
        elapsed = model.run_transactions(threads)
        final_balance = account.get_balance()
        row = _build_summary_row(name, elapsed, final_balance, expected_balance, start_balance)
        row["throughput_per_sec"] = (len(transaction_data) / elapsed) if elapsed > 0 else 0.0
        if baseline_time is None:
            baseline_time = elapsed
        row["speedup_vs_many_to_one"] = (baseline_time / elapsed) if elapsed > 0 and baseline_time else 1.0
        results[name] = row
 
    # ── Print comparison table ──
    print(f"\n{'='*50}")
    print("  CONCURRENCY COMPARISON")
    print(f"{'='*50}")
    print(f"  {'Model':<20} {'Time (s)':<10} {'Tx/s':<8} {'Expected':<10} {'Actual':<10} {'Error':<8} {'Speedup':<8}")
    print(f"  {'-'*82}")
    for name, r in results.items():
        print(
            f"  {name:<20} {r['time']:<10.2f} {r['throughput_per_sec']:<8.2f} ₹{r['expected_balance']:<9} "
            f"₹{r['final_balance']:<9} {r['balance_error']:<8} {r['speedup_vs_many_to_one']:<8.2f}"
        )
    print(f"{'='*50}")
    print(f"  Correct final balance: ₹{expected_balance}")
    print(f"  Starting balance     : ₹{start_balance}")
    print(f"  Net transaction delta: ₹{expected_balance - start_balance}")
    print(f"{'='*50}\n")

    return results



# Add at the very end of thread_model.py
if __name__ == "__main__":
    from bank_account import BankAccount
    
    # Create test transactions
    test_transactions = [
        ("deposit", 500),
        ("withdraw", 200),
        ("deposit", 300),
        ("withdraw", 100),
        ("deposit", 400),
    ]
    
    # Run comparison
    compare_models(BankAccount, test_transactions)
