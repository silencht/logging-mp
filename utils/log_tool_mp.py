import logging
from logging.handlers import QueueHandler, QueueListener
import multiprocessing
from rich.logging import RichHandler
import time

class logging_mp:
    _log_queue = None
    _listener = None

    NOTSET = logging.NOTSET
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL

    class _MonotonicFormatter(logging.Formatter):
        def __init__(self, fmt=None, datefmt=None):
            super().__init__(fmt=fmt, datefmt=datefmt)

        def formatTime(self, record, datefmt=None):
            return f"{time.monotonic():.6f}s"

    @classmethod
    def basic_Config(cls, log_file=None, use_file_handler=True, use_rich_handler=True, level=logging.INFO, format_str=None):
        """Set up the log listener in the main process.

        Parameters:
            log_file (str, optional): Path to the log file. Required if use_file_handler is True.
            use_file_handler (bool): Whether to use FileHandler for file output.
            use_rich_handler (bool): Whether to use RichHandler for terminal output.
            level (int): Logging level, default is INFO.
            format_str (str): Log format string for FileHandler.
        """
        if cls._log_queue is None:
            cls._log_queue = multiprocessing.Queue(-1)

        root = logging.getLogger()
        root.setLevel(level)

        rich_handler = RichHandler(
            show_time=True,
            log_time_format="%H:%M:%S:%f",
            omit_repeated_times=True,
            show_level=True,
            show_path=True,
            rich_tracebacks=True,
            markup=False
        )
        formatter = cls._MonotonicFormatter(format_str)
        rich_handler.setLevel(level)
        rich_handler.setFormatter(formatter)
        root.addHandler(rich_handler)
        
        cls._listener = QueueListener(cls._log_queue, rich_handler, respect_handler_level=True)
        cls._listener.start()

    @classmethod
    def configure_worker_logging(cls):
        """Configure logging for worker processes."""
        if cls._log_queue is None:
            raise RuntimeError("Listener not set up. Please call setup_listener first.")
        root = logging.getLogger()
        for h in root.handlers[:]:
            root.removeHandler(h)
        queue_handler = QueueHandler(cls._log_queue)
        root.addHandler(queue_handler)
        root.setLevel(logging.DEBUG)

    @classmethod
    def get_Logger(cls, name=None):
        """Get a logger instance.

        Parameters:
            name (str, optional): Name of the logger.

        Returns:
            logging.Logger: Configured logger instance.
        """
        return logging.getLogger(name)

    @classmethod
    def stop_listener(cls):
        """Stop the log listener and clean up resources."""
        if cls._listener:
            cls._listener.enqueue_sentinel()
            cls._listener.stop()
            cls._listener = None

        if cls._log_queue:
            try:
                cls._log_queue.close()
                cls._log_queue.join_thread()
            except Exception as e:
                print("Queue cleanup error:", e)
            finally:
                cls._log_queue = None