# logging_mp/__init__.py
import logging
from logging.handlers import QueueHandler, QueueListener
from rich.logging import RichHandler
import multiprocessing
import threading
import atexit
import signal
import os
import sys
import glob
import datetime


# ----------------------------------------------------------------------
# Internal Helpers
# ----------------------------------------------------------------------
class SimpleQueueProxy:
    def __init__(self, queue):
        self._queue = queue
    def put_nowait(self, item): self._queue.put(item)
    def put(self, item): self._queue.put(item)
    def get(self, block=True, timeout=None): return self._queue.get()
    def qsize(self): return 0

def _get_prog_name():
    try:
        name = os.path.splitext(os.path.basename(sys.argv[0]))[0]
        return name if name else "app"
    except:
        return "app"
    
# ----------------------------------------------------------------------
# module-level, spawn-safe
# ----------------------------------------------------------------------
_RAW_LOG_QUEUE = multiprocessing.SimpleQueue()
_LOG_QUEUE = SimpleQueueProxy(_RAW_LOG_QUEUE)

# ----------------------------------------------------------------------
# Main Class
# ----------------------------------------------------------------------
class LoggingMP:
    def __init__(self):
        self._log_queue = None
        self._listener_process = None
        self._stop_event = None
        self._global_level: int = logging.WARNING
        self._is_started: bool = False
        self._lock = threading.Lock()
        self._config = {
            "console": True,
            "file": False,
            "file_path": "logs",
            "backupCount": 10,
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def basicConfig(self, level=logging.WARNING, console=True, file=False, file_path="logs", backupCount=5):
        if self._is_started:
            raise RuntimeError("Logging system has already been started. Please configure before any getLogger() occurs.")
        self._global_level = level
        self._config.update({
            "console": console,
            "file": file,
            "file_path": file_path,
            "backupCount": backupCount
        })
        if not console and not file:
            raise ValueError("At least one of 'console' or 'file' must be True.")
        
        logging.getLogger().setLevel(level)
        self._ensure_started()

    def getLogger(self, name=None):
        self._ensure_started()
        logger = logging.getLogger(name)

        has_handler = any(isinstance(h, QueueHandler) for h in logger.handlers)
        if not has_handler and self._log_queue:
            logger.handlers.clear()
            handler = QueueHandler(self._log_queue)
            logger.setLevel(self._global_level)
            logger.addHandler(handler)
            logger.propagate = False
        return logger

    # ------------------------------------------------------------------
    # Internal Logic
    # ------------------------------------------------------------------
    def _set_queue(self, queue):
        self._log_queue = queue
        # 同时必须更新全局变量，防止其他直接引用
        global _LOG_QUEUE
        _LOG_QUEUE = queue

    @staticmethod
    def _run_listener(queue_proxy, stop_event, config, prog_name):
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        signal.signal(signal.SIGTERM, signal.SIG_IGN)

        handlers = []
        if config.get("console", True):
            handlers.append(
                RichHandler(
                    show_time=True,
                    log_time_format="%H:%M:%S.%f",
                    omit_repeated_times=True,
                    show_level=True,
                    show_path=True,
                    rich_tracebacks=True,
                    markup=False
                )
            )

        if config.get("file", False):
            file_path = config.get("file_path", "logs")
            backupCount = config.get("backupCount", 5)
            os.makedirs(file_path, exist_ok=True)
            log_file_pattern = os.path.join(file_path, f"{prog_name}_*.log")
            old_logs = sorted(glob.glob(log_file_pattern), key=os.path.getmtime)
            
            if len(old_logs) >= backupCount:
                for i in range(len(old_logs) - backupCount + 1):
                    try:
                        os.remove(old_logs[i])
                    except:
                        pass
            
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"{prog_name}_{timestamp}.log"
            file_path = os.path.join(file_path, file_name)
            
            file_handler = logging.FileHandler(file_path, encoding='utf-8')
            file_handler.setFormatter(logging.Formatter(
                fmt='%(asctime)s.%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(processName)s-%(threadName)s: %(message)s',
                datefmt='%H:%M:%S'
            ))
            handlers.append(file_handler)
        
        if not handlers:
            handlers.append(logging.NullHandler())

        listener = QueueListener(queue_proxy, *handlers, respect_handler_level=False)
        listener.start()
        stop_event.wait()
        listener.stop()

    def _ensure_started(self):
        with self._lock:
            if self._is_started: return
            if self._log_queue is None: self._log_queue = _LOG_QUEUE

            if multiprocessing.current_process().name == "MainProcess":
                if self._listener_process is None:
                    self._stop_event = multiprocessing.Event()
                    prog_name = _get_prog_name()
                    
                    self._listener_process = multiprocessing.Process(
                        target=self._run_listener,
                        args=(self._log_queue, self._stop_event, self._config, prog_name),
                        name="LogListenerProcess",
                        daemon=False
                    )
                    self._listener_process.start()
                    atexit.register(self._shutdown)

            self._is_started = True

    def _shutdown(self):
        if not multiprocessing.current_process().name == "MainProcess": return
        if self._stop_event:
            try: self._stop_event.set()
            except: pass
        if self._listener_process: self._listener_process.join()
        self._is_started = False

# ----------------------------------------------------------------------
# Export
# ----------------------------------------------------------------------
NOTSET = logging.NOTSET
DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL

_mp = LoggingMP()
basicConfig = _mp.basicConfig
getLogger = _mp.getLogger