import logging_mp
logger_mp = logging_mp.get_logger(__name__, level=logging_mp.DEBUG)

def worker_pa():
    logger_mp.debug("Detailed debug info")
    logger_mp.info("General information")
    logger_mp.warning("Warning message")
    logger_mp.error("Error occurred")
    logger_mp.critical("Critical failure")
