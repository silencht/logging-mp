from utils.logging_mt import logging_mt
import time
import threading

logging_mt = logging_mt.get_logger(__name__)

def thread_task(thread_id):
    logging_mt.info(f"[Thread-{thread_id}] Hello from a thread!")
    time.sleep(0.1)
    logging_mt.warning(f"[Thread-{thread_id}] Still running...")

def worker_ta():
    logging_mt.info("Starting worker A")
    threads = []
    for i in range(3):
        t = threading.Thread(target=thread_task, args=(i,))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
    logging_mt.info("Worker A finished.")