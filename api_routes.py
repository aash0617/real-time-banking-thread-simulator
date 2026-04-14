"""
api_routes.py - API routes for FastAPI server
Integrates all project components
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import time
import threading
import sys
import io

from bank_account import BankAccount
from transaction_thread import TransactionThread
from scheduler import RoundRobinScheduler

router = APIRouter()

# Request/Response Models
class TransactionRequest(BaseModel):
    type: str  # "deposit" or "withdraw"
    amount: int

class SchedulerSimulateRequest(BaseModel):
    initial_balance: int = 1000
    time_quantum: float = 1.0
    transactions: List[TransactionRequest]

class CompareModelsRequest(BaseModel):
    transactions: Optional[List[tuple]] = None

@router.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok", "service": "Banking Simulator API"}

@router.post("/scheduler/simulate")
async def scheduler_simulate(request: SchedulerSimulateRequest):
    """
    Run Round Robin scheduler with TransactionThreads
    Demonstrates CPU scheduling with context switching
    """
    if not request.transactions:
        raise HTTPException(status_code=400, detail="No transactions provided")
    
    # Create bank account
    account = BankAccount("SCHEDULER_ACC", request.initial_balance)
    
    # Create TransactionThreads
    threads = []
    for i, txn in enumerate(request.transactions):
        thread = TransactionThread(
            thread_id=i + 1,
            account=account,
            txn_type=txn.type,
            amount=txn.amount,
            processing_time=1  # 1 second processing time
        )
        threads.append(thread)
    
    # Create and run scheduler
    scheduler = RoundRobinScheduler(time_quantum=request.time_quantum)
    
    for thread in threads:
        scheduler.add_thread(thread)
    
    # Capture print output
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    
    try:
        scheduler.run()
        scheduler_output = sys.stdout.getvalue()
    finally:
        sys.stdout = old_stdout
    
    # Get metrics
    metrics = scheduler.get_metrics()
    
    return {
        "status": "completed",
        "final_balance": account.get_balance(),
        "transaction_log": account.get_log(),
        "scheduler_metrics": metrics,
        "console_output": scheduler_output
    }

@router.post("/thread-models/compare")
async def compare_thread_models():
    """
    Compare Many-to-One, One-to-One, and Many-to-Many thread mapping models
    Demonstrates different user-to-kernel thread mapping strategies
    """
    from thread_model import compare_models
    
    # Define test transactions
    test_transactions = [
        ("deposit", 500),
        ("withdraw", 200),
        ("deposit", 300),
        ("withdraw", 100),
        ("deposit", 400),
    ]
    
    # Capture printed output
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    
    try:
        results = compare_models(BankAccount, test_transactions)
        output = sys.stdout.getvalue()
    finally:
        sys.stdout = old_stdout
    
    # Format results for API response
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
    
    return {
        "status": "completed",
        "results": formatted_results,
        "console_output": output,
        "explanation": {
            "many_to_one": "Sequential - 1 worker handles all transactions (slowest)",
            "one_to_one": "Parallel - Each transaction gets its own OS thread (fastest)",
            "many_to_many": "Pooled - 3 workers handle 5 transactions (balanced)"
        }
    }

@router.post("/sync-demo")
async def sync_demo():
    """
    Run thread safety demonstration
    Shows race conditions vs thread-safe operations
    """
    from synchronization import demo_race_condition, demo_safe_execution
    
    # Capture printed output
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    
    try:
        unsafe_result = demo_race_condition()
        safe_result = demo_safe_execution()
        output = sys.stdout.getvalue()
    finally:
        sys.stdout = old_stdout
    
    return {
        "status": "completed",
        "unsafe_balance": unsafe_result,
        "safe_balance": safe_result,
        "expected_balance": 2000,
        "money_lost": max(0, 2000 - unsafe_result),
        "console_output": output,
        "explanation": "Without locks, race conditions cause money to be lost. With locks, all transactions are atomic."
    }

@router.get("/project-summary")
async def project_summary():
    """Get summary of all project features"""
    return {
        "project": "Real-Time Multithreaded Banking Transaction Simulator",
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
            },
            {
                "name": "FastAPI Server",
                "file": "main.py + api_routes.py",
                "description": "Modern API with auto-documentation"
            }
        ],
        "endpoints": {
            "flask": "http://localhost:5000",
            "fastapi": "http://localhost:8000",
            "fastapi_docs": "http://localhost:8000/docs"
        }
    }
