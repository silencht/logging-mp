from utils.log_tool_mp import logging_mp

def worker_pb():
    logging_mp.configure_worker_logging()
    logger_mp = logging_mp.get_Logger(__name__)
    logger_mp.debug("Detailed debug info")
    logger_mp.info("General information")
    logger_mp.warning("Warning message")
    logger_mp.error("Error occurred")
    logger_mp.critical("Critical failure")