import logging
from logging.handlers import QueueHandler, QueueListener
import multiprocessing
from rich.logging import RichHandler
import atexit

class logging_mp:
    _log_queue = None
    _listener_processer = None
    _queue_listener = None
    _stop_process_event = None

    # DEBUG => INFO => WARNING => ERROR => CRITICAL
    NOTSET = logging.NOTSET
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL

    @classmethod
    def _is_main_process(cls):
        return multiprocessing.current_process().name == "MainProcess"

    @classmethod
    def _listener_process(cls, queue, _stop_process_event):
        rich_handler = RichHandler(
            show_time=True,
            log_time_format="%H:%M:%S:%f",
            omit_repeated_times=True,
            show_level=True,
            show_path=True,
            rich_tracebacks=True,
            markup=False
        )
        cls._queue_listener = QueueListener(queue, rich_handler, respect_handler_level=False)
        cls._queue_listener.start()
        _stop_process_event.wait()
        cls._queue_listener.stop()
        return
    
    @classmethod
    def basic_config(cls, level=logging.WARNING):
        """
        Set the basic configuration for the logging module.
        This is a no-op in this implementation as the configuration is handled by the listener process.
        """
        root_logger = logging.getLogger()
        root_logger.setLevel(level)

    @classmethod
    def get_logger(cls, name=None, level=None):
        if cls._log_queue is None:
            cls._log_queue = multiprocessing.Queue(-1)

        if cls._is_main_process() and cls._listener_processer is None:
            cls._stop_process_event = multiprocessing.Event()
            cls._listener_processer = multiprocessing.Process(
                    target=cls._listener_process,
                    args=(cls._log_queue, cls._stop_process_event),
                    name="LogListenerProcess",
                    daemon=True
            )
            cls._listener_processer.start()
            atexit.register(cls.stop_listener_process)

        queue_handler = QueueHandler(cls._log_queue)
        logger = logging.getLogger(name)
        if not any(isinstance(h, QueueHandler) for h in logger.handlers):
            logger.handlers.clear()
            if level is not None:
                logger.setLevel(level)
            logger.propagate = False
            logger.addHandler(queue_handler)
        return logger

    @classmethod
    def stop_listener_process(cls):
        if cls._listener_processer and cls._listener_processer.is_alive():
            try:
                cls._stop_process_event.set()
                cls._listener_processer.join()
            except Exception:
                pass

        if cls._log_queue:
            try:
                cls._log_queue.close()
                cls._log_queue.join_thread()
            except Exception:
                pass
            finally:
                cls._log_queue = None