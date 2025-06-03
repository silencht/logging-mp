from utils.log_tool_mp import logging_mp
logger = logging_mp.get_Logger(__name__)

def worker_b():
    logger.debug("Detailed debug info")
    logger.info("General information")
    logger.warning("Warning message")
    logger.error("Error occurred")
    logger.critical("Critical failure")
