import logging_mp
logger_mp = logging_mp.getLogger(__name__)
logger_mp.setLevel(logging_mp.DEBUG) # Individual logger level can be set in worker processes/threads
def worker_tb():
    logger_mp.debug("B: Detailed debug info")
    logger_mp.info("B: General information")
    logger_mp.warning("B: Warning message")
    logger_mp.error("B: Error occurred")
    logger_mp.critical("B: Critical failure")