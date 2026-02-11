# logging_mp/__init__.py
import atexit
import datetime
import glob
import logging
import multiprocessing
import os
import platform
import signal
import sys
import threading
from logging.handlers import QueueHandler, QueueListener
from rich.logging import RichHandler


# ----------------------------------------------------------------------
# Module-level variables
# ----------------------------------------------------------------------
_logging_mp_raw_log_queue = None
_logging_mp_log_queue = None

# ----------------------------------------------------------------------
# Internal Helpers
# ----------------------------------------------------------------------
class _logging_mp_SimpleQueueProxy:
    def __init__(self, queue):
        self._queue = queue
    def put_nowait(self, item): self._queue.put(item)
    def put(self, item): self._queue.put(item)
    def get(self, block=True, timeout=None): return self._queue.get()
    def qsize(self): return 0

def _logging_mp_get_prog_name():
    try:
        name = os.path.splitext(os.path.basename(sys.argv[0]))[0]
        return name if name else "app"
    except Exception:
        return "app"

# ----------------------------------------------------------------------
# Listener and Wrapper Functions
# ----------------------------------------------------------------------
def _logging_mp_queue_listener(queue_proxy, stop_event, config, prog_name):
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
                except Exception:
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

def _logging_mp_target_wrapper(queue, level, original_target, *args, **kwargs):
    global _logging_mp_raw_log_queue, _logging_mp_log_queue
    _logging_mp_raw_log_queue = queue
    _logging_mp_log_queue = queue
    _internal_manager._global_level = level
    _internal_manager._is_started = True
    _internal_manager._log_queue = _logging_mp_log_queue
    # Reconfigure existing loggers (add handler, but preserve levels)
    for name in list(logging.Logger.manager.loggerDict.keys()):
        logger = logging.getLogger(name)
        logger.handlers = [h for h in logger.handlers if not isinstance(h, QueueHandler)]
        if _internal_manager._log_queue:
            handler = QueueHandler(_internal_manager._log_queue)
            logger.addHandler(handler)
        logger.propagate = False
    original_target(*args, **kwargs)

# ----------------------------------------------------------------------
# Main Class
# ----------------------------------------------------------------------
class LoggingMP:
    """Multiprocessing-safe logging manager with queue-based aggregation."""
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
    def basicConfig(
            self,
            level: int = logging.WARNING,
            console: bool = True,
            file: bool = False,
            file_path: str = "logs",
            backupCount: int = 10
        ) -> None:
        """Configure the logging-mp system with global settings.
    
        Args:
            level (int): The global logging level (default: WARNING).
            console (bool): Enable console output (default: True).
            file (bool): Enable file output (default: False).
            file_path (str): Path for log files (default: "logs").
            backupCount (int): Number of backup log files to keep (default: 10).
        
        Raises:
            RuntimeError: If logging is already started.
            ValueError: If neither console nor file is enabled.
        """
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

    def getLogger(
            self, 
            name: str = None
        ) -> logging.Logger:
        """Get a logger instance configured for multiprocessing.
    
        Args:
            name (str, optional): The name of the logger (default: root logger).
        
        Returns:
            logging.Logger: A configured logger that sends logs to the central queue.
        
        Note:
            This clears existing handlers and adds a QueueHandler. Call after basicConfig.
        """
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
    def _ensure_started(self):
        with self._lock:
            if self._is_started: return
            start_method = multiprocessing.get_start_method(allow_none=True)
            if start_method is None:
                start_method = 'spawn' if platform.system() == 'Windows' else 'fork'
            global _logging_mp_raw_log_queue, _logging_mp_log_queue
            if _logging_mp_raw_log_queue is None:
                if start_method == 'fork':
                    _logging_mp_raw_log_queue = multiprocessing.SimpleQueue()
                else:
                    _logging_mp_raw_log_queue = multiprocessing.Queue(-1)
    
            if start_method == 'fork':
                _logging_mp_log_queue = _logging_mp_SimpleQueueProxy(_logging_mp_raw_log_queue)
            else:
                _logging_mp_log_queue = _logging_mp_raw_log_queue

            self._log_queue = _logging_mp_log_queue

            if multiprocessing.current_process().name == "MainProcess":
                if self._listener_process is None:
                    self._stop_event = multiprocessing.Event()
                    prog_name = _logging_mp_get_prog_name()
                    
                    self._listener_process = multiprocessing.Process(
                        target=_logging_mp_queue_listener,
                        args=(_logging_mp_log_queue, self._stop_event, self._config, prog_name),
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
            except Exception: pass
        if self._listener_process: self._listener_process.join(timeout=5)
        self._is_started = False

# ----------------------------------------------------------------------
# Export User-Facing API
# ----------------------------------------------------------------------
NOTSET = logging.NOTSET
DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL

_internal_manager = LoggingMP()
basicConfig = _internal_manager.basicConfig
getLogger = _internal_manager.getLogger

# ----------------------------------------------------------------------
# Patch for Spawn Compatibility
# ----------------------------------------------------------------------
def _apply_spawn_patch():
    start_method = multiprocessing.get_start_method(allow_none=True)
    if start_method is None:
        start_method = 'spawn' if platform.system() == 'Windows' else 'fork'
    if start_method in ('spawn', 'forkserver'):
        original_init = multiprocessing.Process.__init__
        def _logging_mp_patch_init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            global _logging_mp_raw_log_queue
            if _logging_mp_raw_log_queue is not None and self._target is not _logging_mp_queue_listener:
                self._logging_mp_queue = _logging_mp_raw_log_queue
                original_target = self._target
                self._target = _logging_mp_target_wrapper
                self._args = (_logging_mp_raw_log_queue, _internal_manager._global_level, original_target) + self._args

        multiprocessing.Process.__init__ = _logging_mp_patch_init

        original_bootstrap = multiprocessing.Process._bootstrap
        def _logging_mp_patch_bootstrap(self, *args, **kwargs):
            global _logging_mp_raw_log_queue, _logging_mp_log_queue
            try:
                if hasattr(self, '_logging_mp_queue') and self._logging_mp_queue is not None:
                    _logging_mp_raw_log_queue = self._logging_mp_queue
                    _logging_mp_log_queue = self._logging_mp_queue  # Since no proxy for Queue
            except Exception:
                pass
            return original_bootstrap(self, *args, **kwargs)

        multiprocessing.Process._bootstrap = _logging_mp_patch_bootstrap

_apply_spawn_patch()