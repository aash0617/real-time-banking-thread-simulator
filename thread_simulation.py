import threading
import time

def transaction(name):
    print(f"{name} started transaction")
    time.sleep(2)
    print(f"{name} completed transaction")

def main():
    t1 = threading.Thread(target=transaction, args=("User1",))
    t2 = threading.Thread(target=transaction, args=("User2",))

    t1.start()
    t2.start()

    t1.join()
    t2.join()

    print("All transactions completed")

if __name__ == "__main__":
    main()    