import threading
 
 
class BankAccount:
    """
    Thread-safe bank account using a Lock (mutex / binary semaphore).
 
    The lock ensures only ONE thread can read or modify the balance
    at a time — preventing race conditions.
 
    This is the SAFE version. See synchronization.py for the unsafe
    comparison demo.
    """
 
    def __init__(self, account_id, balance=0):
        self.account_id = account_id
        self.balance = balance
        self.lock = threading.Lock()   # the mutex (semaphore)
        self.log = []                  # transaction history
 
    def deposit(self, amount):
        """
        Deposit amount into the account.
        Lock is held for the entire read-modify-write sequence.
        """
        if amount <= 0:
            return
 
        with self.lock:                # acquire lock — only one thread enters
            self.balance += amount
            entry = f"[{self.account_id}] DEPOSIT  ₹{amount:>8} → Balance: ₹{self.balance}"
            self.log.append(entry)
            print(f"  {entry}")
                                       # lock auto-released here
 
    def withdraw(self, amount):
        """
        Withdraw amount from the account if sufficient balance exists.
        Lock is held for the entire check-and-modify sequence.
        """
        if amount <= 0:
            return
 
        with self.lock:                # acquire lock
            if self.balance >= amount:
                self.balance -= amount
                entry = f"[{self.account_id}] WITHDRAW ₹{amount:>8} → Balance: ₹{self.balance}"
                self.log.append(entry)
                print(f"  {entry}")
            else:
                entry = f"[{self.account_id}] FAILED   ₹{amount:>8}   Balance: ₹{self.balance} (insufficient)"
                self.log.append(entry)
                print(f"  {entry}")
                                       # lock auto-released here
 
    def get_balance(self):
        """Thread-safe balance read."""
        with self.lock:
            return self.balance
 
    def get_log(self):
        """Return full transaction log as a list of strings."""
        return list(self.log)
 
    def print_log(self):
        """Print the full transaction history."""
        print(f"\n  Transaction log for account [{self.account_id}]:")
        print(f"  {'─'*50}")
        for entry in self.log:
            print(f"  {entry}")
        print(f"  {'─'*50}")
        print(f"  Final balance: ₹{self.balance}\n")
 
    def __repr__(self):
        return f"BankAccount(id={self.account_id}, balance=₹{self.balance})"
