import logging_mp
logger_mp = logging_mp.getLogger(__name__)
def worker_tc():
    logger_mp.debug("C: Detailed debug info")
    logger_mp.info("C: General information")
    logger_mp.warning("C: Warning message")
    logger_mp.error("C: Error occurred")
    logger_mp.critical("C: Critical failure")
