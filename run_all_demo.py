"""
run_all_demos.py - Run all project demonstrations
Complete integration test for the banking simulator
"""

import subprocess
import sys
import time

def print_header(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def run_demo(name, command, wait_for_key=True):
    print_header(name)
    print(f"Running: {command}\n")
    
    if wait_for_key:
        print("Press Enter to start this demo...")
        input()
    
    result = subprocess.run(command, shell=True)
    
    if result.returncode != 0:
        print(f"\n⚠️ Warning: {name} exited with code {result.returncode}")
    
    return result.returncode

def main():
    print_header("BANKING TRANSACTION SIMULATOR - COMPLETE DEMO")
    print("\nThis will run all demonstrations in sequence.\n")
    print("Available demos:")
    print("  1. Thread Safety Demo (Race Conditions)")
    print("  2. Thread Models Comparison (Many-to-One, One-to-One, Many-to-Many)")
    print("  3. ML Transaction Predictor")
    print("  4. Flask Web Server (starts server - press Ctrl+C to stop)")
    print("  5. FastAPI Server (starts server - press Ctrl+C to stop)")
    print("  6. Run ALL demos sequentially")
    print("  7. Exit")
    
    choice = input("\nEnter your choice (1-7): ")
    
    if choice == "1":
        run_demo("Thread Safety Demo", "python synchronization.py", True)
    
    elif choice == "2":
        run_demo("Thread Models Comparison", "python thread_model.py", True)
    
    elif choice == "3":
        run_demo("ML Transaction Predictor", "python ml_evaluation.py", True)
    
    elif choice == "4":
        print_header("Flask Web Server")
        print("Starting Flask server at http://localhost:5000")
        print("Press Ctrl+C to stop the server\n")
        subprocess.run("python backend_server.py", shell=True)
    
    elif choice == "5":
        print_header("FastAPI Server")
        print("Starting FastAPI server at http://localhost:8000")
        print("API docs available at http://localhost:8000/docs")
        print("Press Ctrl+C to stop the server\n")
        subprocess.run("uvicorn main:app --reload --port 8000", shell=True)
    
    elif choice == "6":
        # Run all demos except servers
        run_demo("Thread Safety Demo", "python synchronization.py", False)
        time.sleep(1)
        run_demo("Thread Models Comparison", "python thread_model.py", False)
        time.sleep(1)
        run_demo("ML Transaction Predictor", "python ml_evaluation.py", False)
        
        print_header("All Demos Completed")
        print("\n✅ All standalone demos have been executed!")
        print("\nTo run the web servers:")
        print("  Flask:  python backend_server.py")
        print("  FastAPI: uvicorn main:app --reload --port 8000")
    
    elif choice == "7":
        print("Exiting...")
    
    else:
        print("Invalid choice!")

if __name__ == "__main__":
    main()
