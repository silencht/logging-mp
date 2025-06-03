from utils.log_tool_mp import logging_mp
logger_mp = logging_mp.get_Logger(__name__)

def processor_pc():
    logger_mp.debug("Detailed debug info")
    logger_mp.info("General information")
    logger_mp.warning("Warning message")
    logger_mp.error("Error occurred")
    logger_mp.critical("Critical failure")
