import threading
import time
from collections import deque
from typing import Callable, Optional


class JobManager:
    """Ejecuta una tarea en segundo plano (solo una a la vez) y guarda estado/resultado."""

    def __init__(self):
        self._lock = threading.Lock()
        self._running: Optional[str] = None
        self._last = {
            "name": None,
            "status": "idle",
            "started": None,
            "finished": None,
            "error": None,
            "result": None,
        }

    @property
    def running(self) -> bool:
        with self._lock:
            return self._running is not None

    def start(self, name: str, fn: Callable[[], object]) -> bool:
        """Inicia una tarea. Devuelve False si ya hay una corriendo."""
        with self._lock:
            if self._running is not None:
                return False
            self._running = name
            self._last = {
                "name": name,
                "status": "running",
                "started": time.time(),
                "finished": None,
                "error": None,
                "result": None,
            }
        thread = threading.Thread(target=self._worker, args=(fn,), daemon=True)
        thread.start()
        return True

    def _worker(self, fn: Callable[[], object]):
        with self._lock:
            name = self._running
            started = self._last["started"]
        try:
            result = fn()
            with self._lock:
                self._last = {
                    "name": name,
                    "status": "done",
                    "started": started,
                    "finished": time.time(),
                    "error": None,
                    "result": result,
                }
        except Exception as exc:  # noqa: BLE001
            with self._lock:
                self._last = {
                    "name": name,
                    "status": "error",
                    "started": started,
                    "finished": time.time(),
                    "error": str(exc),
                    "result": None,
                }
        finally:
            with self._lock:
                self._running = None

    def status(self) -> dict:
        with self._lock:
            return {"running": self._running, **self._last}

    def cancel(self):  # pragma: no cover - simple helper
        """Marca la tarea como cancelada (no detiene el hilo)."""
        with self._lock:
            if self._running is not None:
                self._last["status"] = "cancelled"
                self._running = None


class LogBuffer:
    """Log en memoria con capacidad limitada, seguro para hilos."""

    def __init__(self, maxlen: int = 2000):
        self._lines = deque(maxlen=maxlen)
        self._lock = threading.Lock()

    def write(self, text):
        with self._lock:
            for line in str(text).splitlines():
                self._lines.append(line.rstrip())

    def tail(self, n: int = 200) -> list:
        with self._lock:
            return list(self._lines)[-n:]

    def clear(self):
        with self._lock:
            self._lines.clear()


JOBS = JobManager()
LOGS = LogBuffer()