from utils.log_tool_mt import logging_mt
logging_mt = logging_mt.get_logger(__name__)

def processor_tc():
    logging_mt.debug("Detailed debug info")
    logging_mt.info("General information")
    logging_mt.warning("Warning message")
    logging_mt.error("Error occurred")
    logging_mt.critical("Critical failure")
