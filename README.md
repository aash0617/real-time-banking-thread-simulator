# 🏦 Real-Time Multithreaded Banking Transaction Simulator

---

## 📌 Project Overview

This project simulates a real-world banking system where multiple users perform transactions (deposit and withdrawal) concurrently. It demonstrates key **Operating System concepts** including multithreading, CPU scheduling, thread mapping models, synchronization (semaphores and monitors), and thread lifecycle management using an interactive web-based GUI and terminal demonstrations.

---

## 🎯 Problem Statement

Develop a simulator to demonstrate multithreading models (Many-to-One, One-to-One, Many-to-Many) and thread synchronization using semaphores and monitors. The simulator should visualize thread states and interactions, providing insights into thread management and CPU scheduling in multi-threaded environments.

In a banking system, multiple users may try to access and modify the same account simultaneously. Without proper synchronization, this can lead to:
- Incorrect account balance
- Race conditions
- Data inconsistency

This project solves these issues using thread synchronization (binary and counting semaphores, monitors) and controlled scheduling algorithms.

---

## 🧠 Operating System Concepts Demonstrated

### 1. Multithreading Models (Thread Mapping)

| Model | Description | Real-World Analogy | Performance |
|-------|-------------|-------------------|-------------|
| **Many-to-One** | Multiple user threads map to a single kernel thread | One bank teller serving all customers | 1 transaction/sec (slowest) |
| **One-to-One** | Each user thread maps to a dedicated kernel thread | One teller per customer (parallel) | 5 transactions/sec (fastest) |
| **Many-to-Many** | N user threads multiplexed over M kernel threads | 3 tellers serving 10 customers | 2.5 transactions/sec (balanced) |

### 2. CPU Scheduling Algorithms

| Algorithm | Description | Visualization |
|-----------|-------------|---------------|
| **Round Robin** | Each thread gets a fixed time quantum; if not finished, re-queued at back | Gantt chart shows cyclic execution |
| **Priority Scheduling** | Higher priority threads (lower number) execute first; preemptive | Gantt chart shows priority-based ordering |

### 3. Thread Lifecycle

Each thread transitions through four states:
NEW → READY → RUNNING → TERMINATED



The UI visualizes these states with color coding:
- **READY** (Amber/Yellow) - Waiting for CPU
- **RUNNING** (Cyan with blink) - Currently executing
- **TERMINATED/DONE** (Green) - Completed
- **NEW** (Gray) - Just created

### 4. Synchronization Mechanisms

| Mechanism | Type | Description | Demonstration |
|-----------|------|-------------|---------------|
| **Binary Semaphore (Mutex)** | Mutual Exclusion | Only 1 thread at a time | BankAccount lock prevents race conditions |
| **Counting Semaphore** | Resource Management | N threads at a time | 3 ATMs serving 10 customers |
| **Monitor** | High-level synchronization | `with lock` pattern | Python's automatic lock acquisition/release |
| **Deadlock** | Circular wait | Two threads waiting for each other's locks | lock_1/lock_2 circular wait demo |

### 5. Context Switching

Each time the CPU switches from one thread to another, the context switch counter increments. The Gantt chart visualizes every context switch as a new colored block.

---

## 🏗️ Project Architecture
┌─────────────────────────────────────────────────────────────────────────────┐
│ PROJECT ARCHITECTURE │
├─────────────────────────────────────────────────────────────────────────────┤
│ │
│ ┌──────────────────────┐ ┌──────────────────────┐ │
│ │ TERMINAL DEMOS │ │ WEB UI DEMOS │ │
│ ├──────────────────────┤ ├──────────────────────┤ │
│ │ thread_model.py │ │ backend_server.py │ │
│ │ synchronization.py │ │ ui_final.html │ │
│ │ ml_evaluation.py │ │ main.py (FastAPI) │ │
│ └──────────┬───────────┘ └──────────┬───────────┘ │
│ │ │ │
│ └──────────────┬───────────────┘ │
│ │ │
│ ┌───────────────▼───────────────┐ │
│ │ SHARED COMPONENTS │ │
│ ├───────────────────────────────┤ │
│ │ bank_account.py (Thread-safe) │ │
│ │ transaction_thread.py │ │
│ │ scheduler.py (Round Robin) │ │
│ │ api_routes.py (FastAPI) │ │
│ └───────────────────────────────┘ │
│ │
└─────────────────────────────────────────────────────────────────────────────┘

text

---

## 📁 Project Modules

| Module | File | Description |
|--------|------|-------------|
| **Thread-Safe Bank Account** | `bank_account.py` | Handles balance operations with `threading.Lock` for synchronization |
| **Transaction Thread** | `transaction_thread.py` | Represents a single transaction as an OS thread |
| **Round Robin Scheduler** | `scheduler.py` | Implements Round Robin CPU scheduling with context switching |
| **Synchronization Demo** | `synchronization.py` | Demonstrates race conditions, mutex, deadlock, counting semaphore |
| **Thread Mapping Models** | `thread_model.py` | Many-to-One, One-to-One, Many-to-Many performance comparison |
| **ML Transaction Predictor** | `ml_evaluation.py` | Random Forest model for transaction success/latency prediction |
| **Flask API Server** | `backend_server.py` | REST API with scheduling and thread model endpoints |
| **FastAPI Server** | `main.py` + `api_routes.py` | Modern API with auto-generated documentation |
| **Web Interface** | `ui_final.html` | Interactive GUI with Gantt chart, thread states, metrics |
| **Integration Runner** | `run_all_demo.py` | Runs all demonstrations sequentially |

---

## 🎨 Features

### Web UI Features
- ✅ Real-time thread state visualization (NEW, READY, RUNNING, TERMINATED)
- ✅ Round Robin and Priority scheduling algorithms
- ✅ Interactive Gantt chart showing execution timeline
- ✅ Ready queue visualization
- ✅ Context switch counter with real-time updates
- ✅ Transaction log with color-coded entries
- ✅ Run history tracking
- ✅ Dark/Light theme toggle
- ✅ Keyboard shortcuts (SPACE to start/pause, R to reset)
- ✅ Race condition demonstration tab

### Terminal Demos
- ✅ Many-to-One, One-to-One, Many-to-Many thread model comparison
- ✅ Performance metrics (time, throughput, speedup)
- ✅ Race condition vs safe execution with locks
- ✅ Deadlock demonstration
- ✅ Counting semaphore (3 ATMs for 10 customers)
- ✅ ML transaction success prediction (87% accuracy)

### Synchronization Demos
- ✅ Binary Semaphore (Mutex) - BankAccount lock
- ✅ Counting Semaphore - Limited resource access
- ✅ Monitor - Python's `with lock` pattern
- ✅ Deadlock - Circular wait condition

---

## 🖥️ GUI Components

| Component | Description |
|-----------|-------------|
| 💰 **Account Balance Display** | Shows current balance with flash effects for deposits (green) and withdrawals (red) |
| 📋 **Transaction Log** | Real-time color-coded log of all transactions |
| 🔄 **Ready Queue** | Visual representation of threads waiting for CPU |
| 🧠 **Thread States** | Color-coded list showing each thread's current state |
| 📊 **Gantt Chart** | Visual timeline of thread execution (color-coded by thread) |
| 🔁 **Context Switch Counter** | Tracks number of times CPU switches between threads |
| 📈 **CPU Utilization Ring** | Visual indicator of CPU/memory utilization |
| 🎮 **Control Panel** | Add transactions, select algorithm, set time quantum |
| 📜 **Run History** | Stores each simulation run with metrics |

---

## 🚀 How to Run

### Prerequisites
```bash
pip install flask flask-cors numpy scikit-learn fastapi uvicorn
Run Web UI (Main Application)
bash
python backend_server.py
Then open browser to: http://localhost:5000

Run FastAPI Server (Alternative)
bash
uvicorn main:app --reload --port 8000
Then visit: http://localhost:8000/docs for auto-generated API documentation

Run Terminal Demos
Demo	Command	What it Shows
Thread Models Comparison	python thread_model.py	Many-to-One, One-to-One, Many-to-Many performance
Synchronization Demo	python synchronization.py	Race conditions, locks, deadlock, counting semaphore
ML Transaction Predictor	python ml_evaluation.py	Random Forest accuracy (87%)
Run All Demos
bash
python run_all_demo.py
🧩 API Endpoints
Flask Server (localhost:5000)
Endpoint	Method	Description
/	GET	Serves web UI
/api/simulate	POST	Runs Round Robin or Priority scheduling
/api/sync-demo	POST	Runs race condition and lock demo
/api/thread-models/compare	POST	Compares Many-to-One, One-to-One, Many-to-Many
/api/scheduler/run	POST	Runs Round Robin scheduler with custom transactions
/api/scheduler/run-simple	POST	Quick scheduler test with hardcoded transactions
/api/project-summary	GET	Returns project information and features
/api/health	GET	Health check
FastAPI Server (localhost:8000)
Endpoint	Method	Description
/docs	GET	Auto-generated Swagger documentation
/api/health	GET	Health check
/api/scheduler/simulate	POST	Run Round Robin scheduler
/api/thread-models/compare	POST	Compare thread mapping models
/api/sync-demo	POST	Run synchronization demo
/api/project-summary	GET	Project information
📊 Sample Output
Thread Models Comparison
text
==================================================
  CONCURRENCY COMPARISON
==================================================
  Model                Time (s)   Tx/s     Speedup
  Many-to-One          5.01       1.00     1.00x
  One-to-One           1.00       4.98     4.99x
  Many-to-Many         2.01       2.49     2.50x
Synchronization Demo
text
Without lock:    ₹1400 (₹600 lost due to race condition)
With lock:       ₹2000 (Correct - lock prevented race conditions)
Counting Semaphore: 3 ATMs serving 10 customers (max 3 concurrent)
Deadlock:        Confirmed - circular wait condition
ML Evaluation
text
Classification Accuracy: 87%
Regression R2 Score: 0.80
Fit Diagnosis: Good fit (no overfitting/underfitting)
📁 File Structure
text
real-time-banking-thread-simulator/
├── backend_server.py      # Flask API server (main application)
├── bank_account.py        # Thread-safe BankAccount with lock
├── transaction_thread.py  # Transaction as Thread class
├── scheduler.py           # Round Robin scheduler
├── synchronization.py     # Race condition, deadlock, semaphore demos
├── thread_model.py        # Many-to-One, One-to-One, Many-to-Many
├── ml_evaluation.py       # ML transaction predictor
├── api_routes.py          # FastAPI routes
├── main.py                # FastAPI application entry point
├── ui_final.html          # Web interface (GUI)
├── run_all_demo.py        # Integration runner
└── README.md              # This file
🧠 Conclusion
This project successfully demonstrates:

Three Thread Mapping Models - Many-to-One (sequential), One-to-One (parallel), Many-to-Many (pooled) with performance comparison showing 5x speedup for One-to-One

CPU Scheduling Algorithms - Round Robin with Gantt chart visualization and Priority scheduling

Thread Synchronization - Binary semaphore (mutex), counting semaphore, monitor pattern, and deadlock detection

Thread Lifecycle Visualization - Real-time color-coded thread states (NEW, READY, RUNNING, TERMINATED)

Machine Learning Integration - Random Forest model predicting transaction success with 87% accuracy

The project provides both an interactive web interface for scheduling visualization and terminal demos for performance comparison, making it a comprehensive educational tool for understanding OS multithreading concepts.

🔮 Future Enhancements
Add more scheduling algorithms (FCFS, SJF, MLFQ)

Deadlock detection and prevention visualization in UI

Real-time thread migration visualization

Distributed transaction processing across multiple servers

Persistent storage for transaction history

User authentication and multi-account support

Real-time performance graphs and charts

👨‍💻 Author
Real-Time Multithreaded Banking Transaction Simulator - An educational project demonstrating Operating System concepts through practical implementation.

📝 License
This project is for educational purposes only.

🎯 Ready to demonstrate! Run python backend_server.py and open http://localhost:5000


