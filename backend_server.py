from __future__ import annotations

import os
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, request, send_file

from bank_account import BankAccount
from synchronization import UnsafeBankAccount


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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
