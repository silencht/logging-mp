from multiprocessing import Process
import threading
from utils.logging_mp import logging_mp

from module_a.worker_pa import worker_pa
from module_a.module_b.worker_pb import worker_pb
from module_c.processor_pc import processor_pc

logging_mp.basic_config(level=logging_mp.WARNING)
logger = logging_mp.get_logger(__name__)


def main():
    try:

        logger.debug("Should not be printed.")
        logger.info("Should not be printed.")
        logger.warning("This is a warning message")
        logger.error("This is an error message")
        logger.critical("This is a critical message")

        processes = []
        for i, target in enumerate([worker_pa, worker_pb, processor_pc]):
            p = Process(target=target, name=f"Process-{i}")
            p.start()
            processes.append(p)
        for p in processes:
            p.join()
        
        threads = []
        for i, target in enumerate([worker_pa, worker_pb, processor_pc]):
            t = threading.Thread(target=target, name=f"Thread-{i}")
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

    except KeyboardInterrupt:
        logger.error("KeyboardInterrupt received, stopping processes.")

if __name__ == "__main__":
    main()
