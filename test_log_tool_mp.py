import time
from multiprocessing import Process
from utils.log_tool_mp import logging_mp

from module_a.worker_pa import worker_pa
from module_a.module_b.worker_pb import worker_pb
from module_c.processor_pc import processor_pc


logger = logging_mp.get_Logger(__name__)

# DEBUG => INFO => WARNING => ERROR => CRITICAL

def main():
    logging_mp.set_Global_Level(logging_mp.INFO)
    logger.warning("=== Global Debug Mode ===")
    worker_pa()
    worker_pb()
    processor_pc()

    logging_mp.set_Level("module_a.module_b.worker_pb", logging_mp.WARNING)
    logging_mp.set_Level("module_c.processor_pc", logging_mp.DEBUG)
    logger.error("=== SubModule worker_pb WARNING Mode + SubModule processor_pc DEBUG Mode ===")
    worker_pa()
    worker_pb()
    processor_pc()

    logger.critical("=== Test Multiprocessing ===")
    processes = []
    for i, target in enumerate([worker_pa, worker_pb, processor_pc]):
        p = Process(target=target, name=f"Process-{i}")
        p.start()
        processes.append(p)

    for p in processes:
        p.join()
    time.sleep(0.5)

if __name__ == "__main__":
    main()
