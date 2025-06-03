import logging
import logging.handlers
import multiprocessing
import sys
import time
import atexit
from multiprocessing import Manager, current_process
from typing import Optional, Any

class logging_mp:
    NOTSET = logging.NOTSET
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL

    _manager: Optional[Any] = None
    _log_queue: Optional[multiprocessing.Queue] = None
    _global_level: Optional[Any] = None
    _module_levels: Optional[Any] = None
    _logger_cache: Optional[Any] = None
    _listener: Optional[logging.handlers.QueueListener] = None
    _listener_initialized: bool = False
    _global_level_set_once: bool = False
    _default_global_level = WARNING

    COLOR_RESET = "\033[0m"
    COLOR_DEFAULT = ""
    COLOR_WARNING = "\033[33m"
    COLOR_ERROR = "\033[31m"
    COLOR_CRITICAL = "\033[1;31m"

    class _ColoredMonotonicFormatter(logging.Formatter):
        def formatTime(self, record: logging.LogRecord, datefmt: Optional[str] = None) -> str:
            """Use monotonic time instead of system clock"""
            return f"{time.monotonic():.6f}s"

        def format(self, record: logging.LogRecord) -> str:
            """Apply color coding based on log level"""
            msg = super().format(record)
            color = logging_mp.COLOR_DEFAULT
            
            if record.levelno >= logging_mp.CRITICAL:
                color = logging_mp.COLOR_CRITICAL
            elif record.levelno >= logging_mp.ERROR:
                color = logging_mp.COLOR_ERROR
            elif record.levelno == logging_mp.WARNING:
                color = logging_mp.COLOR_WARNING
            
            return f"{color}{msg}{logging_mp.COLOR_RESET}" if color else msg

    @classmethod
    def _init_shared_resource(cls):
        if cls._manager is None:
            cls._manager = Manager()
        if cls._log_queue is None:
            cls._log_queue = multiprocessing.Queue(-1)
        if cls._global_level is None:
            cls._global_level = cls._manager.Value('i', cls._default_global_level)
        if cls._module_levels is None:
            cls._module_levels = cls._manager.dict()
        if cls._logger_cache is None:
            cls._logger_cache = {}

    @classmethod
    def _start_listener(cls):
        if cls._listener_initialized:
            return
        formatter = cls._ColoredMonotonicFormatter("[%(asctime)s] [%(levelname)-8s] [%(name)s]: %(message)s")
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)
        cls._listener = logging.handlers.QueueListener(cls._log_queue, handler, respect_handler_level=True)
        cls._listener_initialized = True
        cls._listener.start()
        atexit.register(cls._stop_listener)

    @classmethod
    def _stop_listener(cls):
        if cls._listener_initialized:
            try:
                cls._listener.stop()
                cls._log_queue.close()
                cls._log_queue.join_thread()
            except Exception:
                pass
            cls._listener_initialized = False

    @classmethod
    def _update_logger_level(cls, logger: logging.Logger, name: Any):
        if name in cls._module_levels:
            level = cls._module_levels[name]
        else:
            level = cls._global_level.value
        logger.setLevel(level)


    @classmethod
    def get_Logger(cls, name: Any = None) -> logging.Logger:
        cls._init_shared_resource()
        if current_process().name == "MainProcess":
            cls._start_listener()

        if name in cls._logger_cache:
            return cls._logger_cache[name]

        logger = logging.getLogger(name)
        logger.setLevel(logging_mp.NOTSET)
        if not any(isinstance(h, logging.handlers.QueueHandler) for h in logger.handlers):
            logger.addHandler(logging.handlers.QueueHandler(cls._log_queue))
            logger.propagate = False

        cls._update_logger_level(logger, name)
        cls._logger_cache[name] = logger
        return logger

    @classmethod
    def set_Global_Level(cls, level: int) -> None:
        if current_process().name != "MainProcess":
            raise RuntimeError("Global log level can only be set in main process")
        cls._init_shared_resource()
        if cls._global_level_set_once:
            raise RuntimeError("Global log level can only be set once")
        cls._global_level.value = level
        cls._global_level_set_once = True
        # Update all cached loggers without module override
        for name, logger in cls._logger_cache.items():
            if name not in cls._module_levels:
                logger.setLevel(level)

    @classmethod
    def set_Level(cls, name: Any, level: int) -> None:
        cls._init_shared_resource()
        cls._module_levels[name] = level
        if name in cls._logger_cache:
            cls._logger_cache[name].setLevel(level)