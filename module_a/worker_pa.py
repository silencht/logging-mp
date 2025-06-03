from utils.log_tool_mp import logging_mp
import time
import threading

logger_mp = logging_mp.get_Logger(__name__)

def thread_task(thread_id):
    logger_mp.info(f"[Thread-{thread_id}] Hello from a thread!")
    time.sleep(0.1)
    logger_mp.warning(f"[Thread-{thread_id}] Still running...")

def worker_pa():
    logger_mp.info("Starting worker A")
    threads = []
    for i in range(3):
        t = threading.Thread(target=thread_task, args=(i,))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
    logger_mp.info("Worker A finished.")