from utils.logging_mp import logging_mt
logger = logging_mt.get_logger(__name__)

def add(a, b):
    return a + b

def subtract(a, b):
    return a - b