import time
from multiprocessing import Process
from utils.log_tool_mp import logging_mp

from module_a.worker_pa import worker_pa
from module_a.module_b.worker_pb import worker_pb
from module_c.processor_pc import processor_pc


# DEBUG => INFO => WARNING => ERROR => CRITICAL

def main():
    try:
        logging_mp.basic_Config(
            log_file="test_log_tool_mp.log",
            use_file_handler=True,
            use_rich_handler=True,
            level=logging_mp.INFO,
        )
        logger = logging_mp.get_Logger()
        logger.critical("=== Test Multiprocessing ===")
        logger.warning("Starting worker processes...")
        processes = []
        for i, target in enumerate([worker_pa, worker_pb]):
            p = Process(target=target, name=f"Process-{i}")
            p.start()
            processes.append(p)

        for p in processes:
            p.join()
        time.sleep(0.5)

        processor_pc()
        processor_pc()
    except KeyboardInterrupt:
        logger.error("KeyboardInterrupt received, stopping processes.")
    finally:
        logging_mp.stop_listener()

if __name__ == "__main__":
    main()
