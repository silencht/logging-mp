import logging_mp
logger_mp = logging_mp.getLogger(__name__)
def worker_ta():
    logger_mp.debug("A: Detailed debug info")
    logger_mp.info("A: General information")
    logger_mp.warning("A: Warning message")
    logger_mp.error("A: Error occurred")
    logger_mp.critical("A: Critical failure")


if __name__ == "__main__":
    logger_mp.setLevel(logging_mp.INFO) # Individual logger level can be set in worker processes/threads
    worker_ta()
