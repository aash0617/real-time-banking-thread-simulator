from __future__ import annotations

import os
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, request, send_file

from bank_account import BankAccount
from synchronization import UnsafeBankAccount
from transaction_thread import TransactionThread
from scheduler import RoundRobinScheduler
from thread_model import compare_models


app = Flask(__name__)


@dataclass
class SimThread:
    thread_id: int
    txn_type: str
    amount: int
    processing_time_ms: int
    priority: int
    remaining_ms: int


def _apply_cors(resp):
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return resp


@app.after_request
def _after_request(resp):
    return _apply_cors(resp)


@app.route("/", methods=["GET"])
def index():
    local_ui = Path(__file__).with_name("ui_final.html")
    root_ui = Path(__file__).resolve().parent.parent / "ui_final.html"

    if local_ui.exists():
        return send_file(local_ui)
    if root_ui.exists():
        return send_file(root_ui)

    return (
        jsonify({
            "ok": False,
            "error": "ui_final.html not found",
            "checked": [str(local_ui), str(root_ui)],
        }),
        404,
    )


@app.route("/api/health", methods=["GET", "OPTIONS"])
def health():
    if request.method == "OPTIONS":
        return _apply_cors(jsonify({"ok": True}))
    return jsonify({"ok": True, "service": "banking-simulator-api"})


def _build_threads(raw_threads: list[dict[str, Any]]) -> list[SimThread]:
    built: list[SimThread] = []
    for idx, txn in enumerate(raw_threads, start=1):
        processing_time = int(txn.get("processingTime", 0) or 0)
        built.append(
            SimThread(
                thread_id=int(txn.get("id", idx) or idx),
                txn_type=str(txn.get("type", "deposit")).lower(),
                amount=int(txn.get("amount", 0) or 0),
                processing_time_ms=processing_time,
                priority=int(txn.get("priority", 1) or 1),
                remaining_ms=processing_time,
            )
        )
    return built


def _execute_transaction(balance: int, txn: SimThread) -> tuple[int, int, str, str]:
    if txn.txn_type == "deposit":
        new_balance = balance + txn.amount
        return new_balance, txn.amount, "deposit", f"DEPOSIT Rs{txn.amount}"

    if txn.txn_type == "withdraw":
        if balance >= txn.amount:
            new_balance = balance - txn.amount
            return new_balance, -txn.amount, "withdraw", f"WITHDRAW Rs{txn.amount}"
        return balance, 0, "fail", f"FAILED WITHDRAW Rs{txn.amount} (insufficient)"

    return balance, 0, "sys", f"UNKNOWN TXN TYPE: {txn.txn_type}"


def _simulate_round_robin(threads: list[SimThread], quantum_ms: int, init_balance: int):
    queue = threads[:]
    balance = init_balance
    context_switches = 0
    completed = 0
    slices: list[dict[str, Any]] = []
    logs: list[dict[str, Any]] = []

    while queue:
        thread = queue.pop(0)

        if thread.remaining_ms <= 0:
            continue

        run_ms = min(quantum_ms, thread.remaining_ms)
        thread.remaining_ms -= run_ms
        context_switches += 1

        slice_entry: dict[str, Any] = {
            "threadId": thread.thread_id,
            "runMs": run_ms,
            "event": "requeue",
            "remainingMs": thread.remaining_ms,
            "priority": thread.priority,
            "type": thread.txn_type,
        }

        if thread.remaining_ms <= 0:
            balance, delta, log_type, message = _execute_transaction(balance, thread)
            completed += 1
            slice_entry["event"] = "done"
            slice_entry["delta"] = delta
            slice_entry["balanceAfter"] = balance
            logs.append({"type": log_type, "message": message, "balance": balance})
        else:
            queue.append(thread)

        slices.append(slice_entry)

    return {
        "algorithm": "rr",
        "finalBalance": balance,
        "completedThreads": completed,
        "totalThreads": len(threads),
        "contextSwitches": context_switches,
        "slices": slices,
        "logs": logs,
    }


def _simulate_priority(threads: list[SimThread], quantum_ms: int, init_balance: int):
    balance = init_balance
    context_switches = 0
    completed = 0
    slices: list[dict[str, Any]] = []
    logs: list[dict[str, Any]] = []

    while completed < len(threads):
        candidates = [t for t in threads if t.remaining_ms > 0]
        if not candidates:
            break

        candidates.sort(key=lambda t: (t.priority, t.thread_id))
        thread = candidates[0]

        run_ms = min(quantum_ms, thread.remaining_ms)
        thread.remaining_ms -= run_ms
        context_switches += 1

        slice_entry: dict[str, Any] = {
            "threadId": thread.thread_id,
            "runMs": run_ms,
            "event": "requeue",
            "remainingMs": thread.remaining_ms,
            "priority": thread.priority,
            "type": thread.txn_type,
        }

        if thread.remaining_ms <= 0:
            balance, delta, log_type, message = _execute_transaction(balance, thread)
            completed += 1
            slice_entry["event"] = "done"
            slice_entry["delta"] = delta
            slice_entry["balanceAfter"] = balance
            logs.append({"type": log_type, "message": message, "balance": balance})

        slices.append(slice_entry)

    return {
        "algorithm": "priority",
        "finalBalance": balance,
        "completedThreads": completed,
        "totalThreads": len(threads),
        "contextSwitches": context_switches,
        "slices": slices,
        "logs": logs,
    }


@app.route("/api/simulate", methods=["POST", "OPTIONS"])
def simulate():
    if request.method == "OPTIONS":
        return _apply_cors(jsonify({"ok": True}))

    payload = request.get_json(silent=True) or {}
    algorithm = str(payload.get("algorithm", "rr")).lower()
    quantum_ms = max(1, int(payload.get("quantumMs", 600) or 600))
    init_balance = int(payload.get("initialBalance", 5000) or 5000)
    raw_threads = payload.get("threads", [])

    if not isinstance(raw_threads, list) or len(raw_threads) == 0:
        return jsonify({"ok": False, "error": "No threads provided."}), 400

    threads = _build_threads(raw_threads)

    if algorithm == "priority":
        result = _simulate_priority(threads, quantum_ms, init_balance)
    else:
        result = _simulate_round_robin(threads, quantum_ms, init_balance)

    result["ok"] = True
    return jsonify(result)


def _run_unsafe_demo() -> int:
    unsafe_account = UnsafeBankAccount("UNSAFE_ACC", balance=1000)
    workers = []
    for _ in range(10):
        t = threading.Thread(target=unsafe_account.deposit, args=(100,))
        workers.append(t)
    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join()
    return unsafe_account.get_balance()


def _run_safe_demo() -> int:
    safe_account = BankAccount("SAFE_ACC", balance=1000)
    workers = []
    for _ in range(10):
        t = threading.Thread(target=safe_account.deposit, args=(100,))
        workers.append(t)
    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join()
    return safe_account.get_balance()


@app.route("/api/sync-demo", methods=["POST", "OPTIONS"])
def sync_demo():
    if request.method == "OPTIONS":
        return _apply_cors(jsonify({"ok": True}))

    expected = 2000
    unsafe = _run_unsafe_demo()
    safe = _run_safe_demo()

    return jsonify(
        {
            "ok": True,
            "expected": expected,
            "unsafe": unsafe,
            "safe": safe,
            "lost": max(0, expected - unsafe),
        }
    )


# ============================================================
# NEW INTEGRATED ENDPOINTS
# ============================================================

@app.route("/api/thread-models/compare", methods=["POST", "OPTIONS"])
def api_compare_thread_models():
    """Compare Many-to-One, One-to-One, and Many-to-Many thread models"""
    if request.method == "OPTIONS":
        return _apply_cors(jsonify({"ok": True}))
    
    # Define test transactions
    test_transactions = [
        ("deposit", 500),
        ("withdraw", 200),
        ("deposit", 300),
        ("withdraw", 100),
        ("deposit", 400),
    ]
    
    # Run comparison
    results = compare_models(BankAccount, test_transactions)
    
    # Format results
    formatted_results = {}
    for name, metrics in results.items():
        formatted_results[name] = {
            "time_seconds": metrics["time"],
            "throughput_per_sec": metrics["throughput_per_sec"],
            "final_balance": metrics["final_balance"],
            "expected_balance": metrics["expected_balance"],
            "balance_error": metrics["balance_error"],
            "correct": metrics["correct"],
            "speedup": metrics["speedup_vs_many_to_one"]
        }
    
    return jsonify({
        "ok": True,
        "results": formatted_results,
        "explanation": {
            "many_to_one": "Sequential - 1 worker handles all transactions (slowest)",
            "one_to_one": "Parallel - Each transaction gets its own OS thread (fastest)",
            "many_to_many": "Pooled - 3 workers handle 5 transactions (balanced)"
        }
    })


@app.route("/api/scheduler/run", methods=["POST", "OPTIONS"])
def api_run_scheduler():
    """Run Round Robin scheduler with TransactionThreads"""
    if request.method == "OPTIONS":
        return _apply_cors(jsonify({"ok": True}))
    
    payload = request.get_json(silent=True) or {}
    initial_balance = int(payload.get("initialBalance", 1000))
    time_quantum = float(payload.get("timeQuantum", 1.0))
    transactions_data = payload.get("transactions", [])
    
    if not transactions_data:
        return jsonify({"ok": False, "error": "No transactions provided"}), 400
    
    # Create bank account
    account = BankAccount("SCHEDULER_ACC", initial_balance)
    
    # Create TransactionThreads
    threads = []
    for i, txn in enumerate(transactions_data):
        thread = TransactionThread(
            thread_id=i + 1,
            account=account,
            txn_type=txn.get("type", "deposit"),
            amount=txn.get("amount", 0),
            processing_time=1
        )
        threads.append(thread)
    
    # Create and run scheduler
    scheduler = RoundRobinScheduler(time_quantum=time_quantum)
    
    for thread in threads:
        scheduler.add_thread(thread)
    
    # Run scheduler
    scheduler.run()
    
    # Get metrics
    metrics = scheduler.get_metrics()
    
    return jsonify({
        "ok": True,
        "final_balance": account.get_balance(),
        "transaction_log": account.get_log(),
        "scheduler_metrics": metrics
    })


@app.route("/api/scheduler/run-simple", methods=["POST", "OPTIONS"])
def api_run_scheduler_simple():
    """Run Round Robin scheduler with simple hardcoded transactions for quick testing"""
    if request.method == "OPTIONS":
        return _apply_cors(jsonify({"ok": True}))
    
    payload = request.get_json(silent=True) or {}
    initial_balance = int(payload.get("initialBalance", 1000))
    time_quantum = float(payload.get("timeQuantum", 1.0))
    
    # Hardcoded test transactions
    transactions_data = [
        {"type": "deposit", "amount": 500},
        {"type": "withdraw", "amount": 200},
        {"type": "deposit", "amount": 300},
        {"type": "withdraw", "amount": 100},
        {"type": "deposit", "amount": 400},
    ]
    
    # Create bank account
    account = BankAccount("SCHEDULER_ACC", initial_balance)
    
    # Create TransactionThreads
    threads = []
    for i, txn in enumerate(transactions_data):
        thread = TransactionThread(
            thread_id=i + 1,
            account=account,
            txn_type=txn["type"],
            amount=txn["amount"],
            processing_time=1
        )
        threads.append(thread)
    
    # Create and run scheduler
    scheduler = RoundRobinScheduler(time_quantum=time_quantum)
    
    for thread in threads:
        scheduler.add_thread(thread)
    
    # Run scheduler
    scheduler.run()
    
    # Get metrics
    metrics = scheduler.get_metrics()
    
    return jsonify({
        "ok": True,
        "final_balance": account.get_balance(),
        "transaction_log": account.get_log(),
        "scheduler_metrics": metrics,
        "transactions_processed": len(threads)
    })


@app.route("/api/project-summary", methods=["GET", "OPTIONS"])
def api_project_summary():
    """Get summary of all project features"""
    if request.method == "OPTIONS":
        return _apply_cors(jsonify({"ok": True}))
    
    return jsonify({
        "ok": True,
        "project": "Real-Time Multithreaded Banking Transaction Simulator",
        "version": "2.0.0",
        "features": [
            {
                "name": "Thread-Safe Banking",
                "file": "bank_account.py",
                "description": "BankAccount with threading.Lock for atomic transactions"
            },
            {
                "name": "Race Condition Demo", 
                "file": "synchronization.py",
                "description": "Shows unsafe vs safe account behavior"
            },
            {
                "name": "Round Robin Scheduler",
                "file": "scheduler.py",
                "description": "CPU scheduling simulation with context switching"
            },
            {
                "name": "Transaction Thread",
                "file": "transaction_thread.py",
                "description": "Individual transaction as OS thread"
            },
            {
                "name": "Thread Mapping Models",
                "file": "thread_model.py",
                "description": "Many-to-One, One-to-One, Many-to-Many comparisons"
            },
            {
                "name": "ML Transaction Predictor",
                "file": "ml_evaluation.py",
                "description": "Random Forest for success/latency prediction"
            },
            {
                "name": "Flask API Server",
                "file": "backend_server.py",
                "description": "REST API with Round Robin and Priority scheduling"
            }
        ],
        "endpoints": {
            "simulate_rr_priority": "POST /api/simulate",
            "sync_demo": "POST /api/sync-demo",
            "thread_models": "POST /api/thread-models/compare",
            "scheduler_run": "POST /api/scheduler/run",
            "scheduler_simple": "POST /api/scheduler/run-simple",
            "summary": "GET /api/project-summary",
            "health": "GET /api/health"
        },
        "usage_examples": {
            "compare_thread_models": "curl -X POST http://localhost:5000/api/thread-models/compare",
            "run_scheduler": "curl -X POST http://localhost:5000/api/scheduler/run-simple -H 'Content-Type: application/json' -d '{\"initialBalance\":1000,\"timeQuantum\":1}'",
            "sync_demo": "curl -X POST http://localhost:5000/api/sync-demo"
        }
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
