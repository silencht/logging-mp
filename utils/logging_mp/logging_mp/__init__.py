# logging_mp/__init__.py

import logging
from logging.handlers import QueueHandler, QueueListener
import multiprocessing
from rich.logging import RichHandler
import atexit

_log_queue = None
_listener_processer = None
_queue_listener = None
_stop_process_event = None

NOTSET = logging.NOTSET
DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL

def _is_main_process():
    return multiprocessing.current_process().name == "MainProcess"

def _listener_process(queue, _stop_process_event):
    try:
        global _queue_listener
        rich_handler = RichHandler(
            show_time=True,
            log_time_format="%H:%M:%S:%f",
            omit_repeated_times=True,
            show_level=True,
            show_path=True,
            rich_tracebacks=True,
            markup=False
        )
        _queue_listener = QueueListener(queue, rich_handler, respect_handler_level=False)
        _queue_listener.start()
        _stop_process_event.wait()
    except Exception as e:
        print(f"Error in _listener_process: {e}")
    finally:
        if _queue_listener:
            _queue_listener.stop()

def basic_config(level=logging.WARNING):
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

def get_logger(name=None, level=None):
    global _log_queue, _listener_processer, _stop_process_event

    if _is_main_process() and _log_queue is None and _listener_processer is None:
        _log_queue = multiprocessing.Queue(-1)
        _stop_process_event = multiprocessing.Event()
        _listener_processer = multiprocessing.Process(
            target=_listener_process,
            args=(_log_queue, _stop_process_event),
            name="LogListenerProcess",
            daemon=True
        )
        _listener_processer.start()
        if not hasattr(stop_listener_process, "_registered"):
            atexit.register(stop_listener_process)
            stop_listener_process._registered = True

    queue_handler = QueueHandler(_log_queue)
    logger = logging.getLogger(name)
    if not any(isinstance(h, QueueHandler) and h.queue is _log_queue for h in logger.handlers):
        logger.handlers.clear()
        if level is not None:
            logger.setLevel(level)
        logger.propagate = False
        logger.addHandler(queue_handler)
    return logger

def stop_listener_process():
    global _listener_processer, _log_queue, _stop_process_event
    if _log_queue:
        try:
            while not _log_queue.empty():
                import time
                time.sleep(0.1)
        except Exception as e:
            print(f"Error draining queue: {e}")

    if _listener_processer and _listener_processer.is_alive():
        try:
            _stop_process_event.set()
            _listener_processer.join(timeout=1)
            if _listener_processer.is_alive():
                _listener_processer.terminate()
        except Exception as e:
            print(f"Error stopping listener process: {e}")

    if _log_queue:
        try:
            _log_queue.close()
            _log_queue.join_thread()
        except Exception as e:
            print(f"Error closing queue: {e}")
        finally:
            _log_queue = None
