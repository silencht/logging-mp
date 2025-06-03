import time
from multiprocessing import Process
from utils.log_tool_mp import logging_mp

from module_a.worker_a import worker_a
from module_a.module_b.worker_b import worker_b
from module_c.processor_c import processor_c


logger = logging_mp.get_Logger(__name__)

# DEBUG => INFO => WARNING => ERROR => CRITICAL

def main():
    logging_mp.set_Global_Level(logging_mp.INFO)
    logger.warning("=== Global Debug Mode ===")
    worker_a()
    worker_b()
    processor_c()

    logging_mp.set_Level("module_a.module_b.worker_b", logging_mp.WARNING)
    logging_mp.set_Level("module_c.processor_c", logging_mp.DEBUG)
    logger.error("=== SubModule worker_b WARNING Mode + SubModule processor_c DEBUG Mode ===")
    worker_a()
    worker_b()
    processor_c()

    logger.critical("=== Test Multiprocessing ===")
    processes = []
    for i, target in enumerate([worker_a, worker_b, processor_c]):
        p = Process(target=target, name=f"Process-{i}")
        p.start()
        processes.append(p)

    for p in processes:
        p.join()
    time.sleep(0.5)

if __name__ == "__main__":
    main()
