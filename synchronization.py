import threading
import time
from bank_account import BankAccount


# ─────────────────────────────────────────────────────────────
#  UNSAFE BANK ACCOUNT — for demonstration only
#  Shows what happens WITHOUT synchronization (race condition)
# ─────────────────────────────────────────────────────────────

class UnsafeBankAccount:
    """
    Intentionally unsafe version — NO lock.
    Multiple threads reading and writing balance simultaneously
    will cause race conditions and incorrect final balances.

    DO NOT use this in production. This class exists only to
    demonstrate why synchronization is necessary.
    """

    def __init__(self, account_id, balance=0):
        self.account_id = account_id
        self.balance = balance
        self.log = []

    def deposit(self, amount):
        if amount <= 0:
            return
        # ── RACE CONDITION ZONE ──
        # Thread A reads balance = 1000
        # Thread B reads balance = 1000  (before A writes)
        # Thread A writes 1000 + 500 = 1500
        # Thread B writes 1000 + 300 = 1300  (overwrites A's result!)
        # Final: 1300  — should be 1800!
        current = self.balance         # read
        time.sleep(0.001)              # tiny delay — makes race more likely
        self.balance = current + amount  # write (may overwrite another thread's update)
        self.log.append(f"[UNSAFE] DEPOSIT  ₹{amount} → ₹{self.balance}")

    def withdraw(self, amount):
        if amount <= 0:
            return
        current = self.balance
        time.sleep(0.001)
        if current >= amount:
            self.balance = current - amount
            self.log.append(f"[UNSAFE] WITHDRAW ₹{amount} → ₹{self.balance}")
        else:
            self.log.append(f"[UNSAFE] FAILED   ₹{amount}   Balance: ₹{self.balance}")

    def get_balance(self):
        return self.balance


# ─────────────────────────────────────────────────────────────
#  COUNTING SEMAPHORE DEMO
#  Demonstrates limited resource access (e.g., ATMs)
# ─────────────────────────────────────────────────────────────

class CountingSemaphoreDemo:
    """
    Demonstrates counting semaphore for limited resource access.
    Example: 3 ATMs available for 10 customers.
    
    A counting semaphore allows up to 'n' threads to access
    a resource simultaneously. This is different from a binary
    semaphore (mutex) which only allows 1 thread at a time.
    """

    def __init__(self, available_resources=3):
        self.semaphore = threading.Semaphore(available_resources)
        self.usage_log = []
        self.resource_name = "ATM"

    def use_resource(self, customer_id, resource_type="ATM"):
        """
        Simulate using a limited resource (e.g., ATM, database connection)
        """
        # Wait (P operation) - acquire semaphore
        self.semaphore.acquire()
        
        entry_time = time.strftime('%H:%M:%S')
        self.usage_log.append(f"[{entry_time}] Customer {customer_id} acquired {resource_type}")
        print(f"  [SEMAPHORE] Customer {customer_id} → USING {resource_type}")
        
        # Simulate using the resource
        time.sleep(0.5)
        
        # Signal (V operation) - release semaphore
        self.semaphore.release()
        exit_time = time.strftime('%H:%M:%S')
        self.usage_log.append(f"[{exit_time}] Customer {customer_id} released {resource_type}")
        print(f"  [SEMAPHORE] Customer {customer_id} → RELEASED {resource_type}")

    def run_demo(self, num_customers=10, available_resources=3):
        """
        Run the counting semaphore demonstration.
        
        Args:
            num_customers: Number of threads trying to access resource
            available_resources: How many can access simultaneously
        """
        print("\n" + "="*55)
        print("  DEMO: COUNTING SEMAPHORE")
        print("  ==========================")
        print(f"  {available_resources} resources available for {num_customers} customers")
        print("  Only {available_resources} customers can use the resource at once!")
        print("="*55)

        # Reset semaphore with new count
        self.semaphore = threading.Semaphore(available_resources)
        self.usage_log = []
        
        threads = []
        for i in range(num_customers):
            t = threading.Thread(target=self.use_resource, args=(i+1, "ATM"))
            threads.append(t)
            t.start()
            # Small stagger so not all start at exactly same time
            time.sleep(0.05)

        for t in threads:
            t.join()

        # Print summary
        print("\n  ─── EXECUTION SUMMARY ───")
        for log in self.usage_log:
            print(f"  {log}")
        
        print(f"\n  ✅ At most {available_resources} customers used the resource simultaneously!")
        print("  📌 This demonstrates COUNTING SEMAPHORE — allows N concurrent accesses.")
        
        return len(self.usage_log) // 2  # Return number of successful accesses


# ─────────────────────────────────────────────────────────────
#  DEMO: RACE CONDITION vs SAFE EXECUTION
# ─────────────────────────────────────────────────────────────

def demo_race_condition():
    """
    Runs 10 deposit threads on an unsafe account.
    Expected final balance: 1000 + (10 × 100) = 2000
    Actual result: likely LESS due to race conditions.
    """
    print("\n" + "="*55)
    print("  DEMO 1: WITHOUT synchronization (race condition)")
    print("="*55)

    unsafe_account = UnsafeBankAccount("UNSAFE_ACC", balance=1000)
    expected = 1000 + (10 * 100)

    threads = []
    for i in range(10):
        t = threading.Thread(
            target=unsafe_account.deposit,
            args=(100,),
            name=f"UnsafeThread-{i+1}"
        )
        threads.append(t)

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    actual = unsafe_account.get_balance()
    print(f"\n  Starting balance : ₹1000")
    print(f"  10 deposits of  : ₹100 each")
    print(f"  Expected balance : ₹{expected}")
    print(f"  Actual balance   : ₹{actual}")

    if actual != expected:
        lost = expected - actual
        print(f"\n  ⚠️ RACE CONDITION DETECTED — ₹{lost} was LOST due to overwrites!")
    else:
        print(f"\n  (No race condition detected this run — try again, it's non-deterministic)")

    return actual


def demo_safe_execution():
    """
    Runs 10 deposit threads on a safe (locked) account.
    Expected final balance: 1000 + (10 × 100) = 2000
    Actual result: always 2000 — guaranteed by the lock.
    """
    print("\n" + "="*55)
    print("  DEMO 2: WITH synchronization (threading.Lock)")
    print("="*55)

    safe_account = BankAccount("SAFE_ACC", balance=1000)
    expected = 1000 + (10 * 100)

    threads = []
    for i in range(10):
        t = threading.Thread(
            target=safe_account.deposit,
            args=(100,),
            name=f"SafeThread-{i+1}"
        )
        threads.append(t)

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    actual = safe_account.get_balance()
    print(f"\n  Starting balance : ₹1000")
    print(f"  10 deposits of  : ₹100 each")
    print(f"  Expected balance : ₹{expected}")
    print(f"  Actual balance   : ₹{actual}")

    if actual == expected:
        print(f"\n  ✅ CORRECT — Lock (binary semaphore) prevented all race conditions.")
    else:
        print(f"\n  ❌ Something went wrong — check your lock implementation.")

    return actual


def demo_deadlock():
    """
    OPTIONAL BONUS: Demonstrates a deadlock scenario.

    Thread A holds lock_1, waits for lock_2.
    Thread B holds lock_2, waits for lock_1.
    Neither can proceed — deadlock!

    The program will hang here for 5 seconds to show the deadlock,
    then forcibly stop via daemon threads timing out.
    """
    print("\n" + "="*55)
    print("  DEMO 3 (BONUS): Deadlock scenario")
    print("="*55)
    print("  Thread A: acquire lock_1, then try lock_2")
    print("  Thread B: acquire lock_2, then try lock_1")
    print("  Result  : Both threads wait forever — DEADLOCK")
    print()

    lock_1 = threading.Lock()
    lock_2 = threading.Lock()
    deadlock_detected = threading.Event()

    def thread_a():
        with lock_1:
            print("  [Thread A] Acquired lock_1 — waiting for lock_2...")
            time.sleep(0.5)            # give Thread B time to grab lock_2
            acquired = lock_2.acquire(timeout=3)
            if acquired:
                print("  [Thread A] Got lock_2 (no deadlock this run)")
                lock_2.release()
            else:
                print("  [Thread A] DEADLOCK — could not acquire lock_2 (timeout)")
                deadlock_detected.set()

    def thread_b():
        with lock_2:
            print("  [Thread B] Acquired lock_2 — waiting for lock_1...")
            time.sleep(0.5)
            acquired = lock_1.acquire(timeout=3)
            if acquired:
                print("  [Thread B] Got lock_1 (no deadlock this run)")
                lock_1.release()
            else:
                print("  [Thread B] DEADLOCK — could not acquire lock_1 (timeout)")
                deadlock_detected.set()

    ta = threading.Thread(target=thread_a, daemon=True)
    tb = threading.Thread(target=thread_b, daemon=True)

    ta.start()
    tb.start()
    ta.join(timeout=5)
    tb.join(timeout=5)

    if deadlock_detected.is_set():
        print("\n  🔒 DEADLOCK CONFIRMED — both threads timed out waiting for each other.")
        print("  💡 Solution: always acquire locks in the SAME ORDER in all threads.")
    else:
        print("\n  (Deadlock did not occur this run — timing-dependent)")


# ─────────────────────────────────────────────────────────────
#  RUN ALL DEMOS
# ─────────────────────────────────────────────────────────────

def run_all_sync_demos():
    """
    Run all synchronization demonstrations:
    1. Race condition (unsafe)
    2. Safe execution (with lock)
    3. Deadlock scenario
    4. Counting semaphore (limited resources)
    """
    unsafe_result = demo_race_condition()
    safe_result = demo_safe_execution()

    print("\n" + "="*55)
    print("  SUMMARY: BINARY SEMAPHORE (MUTEX)")
    print("="*55)
    print(f"  Without lock : ₹{unsafe_result}  (may be wrong — race condition)")
    print(f"  With lock    : ₹{safe_result}  (always correct — mutual exclusion)")
    print("="*55)

    demo_deadlock()
    
    # Run counting semaphore demo
    counting_demo = CountingSemaphoreDemo()
    counting_demo.run_demo(num_customers=10, available_resources=3)
    
    print("\n" + "="*55)
    print("  FINAL SUMMARY: SYNCHRONIZATION MECHANISMS")
    print("="*55)
    print("  🔒 Binary Semaphore (Mutex)  : Only 1 thread at a time")
    print("  📊 Counting Semaphore        : N threads at a time (limited resource)")
    print("  🔄 Monitor                   : with lock + condition (Python's 'with lock')")
    print("  ⚠️ Deadlock                   : Circular wait condition")
    print("="*55)


if __name__ == "__main__":
    run_all_sync_demos()

