import time
from multiprocessing import Process
from utils.log_tool_mt import logging_mt

from module_a.worker_ta import worker_ta
from module_a.module_b.worker_tb import worker_tb
from module_c.processor_tc import processor_tc


logger = logging_mt.get_logger(__name__)

# DEBUG => INFO => WARNING => ERROR => CRITICAL

def main():
    logging_mt.set_Global_Level(logging_mt.INFO)
    logger.warning("=== Global Debug Mode ===")
    worker_ta()
    worker_tb()
    processor_tc()

    logging_mt.set_Level("module_a.module_b.worker_tb", logging_mt.WARNING)
    logging_mt.set_Level("module_c.processor_tc", logging_mt.DEBUG)
    logger.error("=== SubModule worker_tb WARNING Mode + SubModule processor_tc DEBUG Mode ===")
    worker_ta()
    worker_tb()
    processor_tc()

    logger.critical("=== Test Multiprocessing ===")
    processes = []
    for i, target in enumerate([worker_ta, worker_tb, processor_tc]):
        p = Process(target=target, name=f"Process-{i}")
        p.start()
        processes.append(p)

    for p in processes:
        p.join()
    time.sleep(0.5)

if __name__ == "__main__":
    main()
