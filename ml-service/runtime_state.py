"""Thread-safe ML readiness state and privacy-safe timing helpers."""

from __future__ import annotations

import math
import re
import threading
import time
from dataclasses import dataclass
from typing import Any, Callable


SERVER_TIMING_NAMES = (
    "model_wait", "embedding", "db_connect", "db_query", "rerank", "ml_total"
)
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9-]{1,64}$")


def safe_request_id(value: str | None) -> str:
    """Return only a bounded opaque request id, never arbitrary header content."""
    return value if value and REQUEST_ID_PATTERN.fullmatch(value) else "none"


def server_timing_header(timings_ms: dict[str, float]) -> str:
    """Serialize only fixed segment names and finite non-negative durations."""
    entries = []
    for name in SERVER_TIMING_NAMES:
        value = timings_ms.get(name)
        if value is None or not math.isfinite(value) or value < 0:
            continue
        entries.append(f"{name};dur={value:.3f}")
    return ", ".join(entries)


@dataclass(frozen=True)
class RuntimeSnapshot:
    status: str
    model_load_ms: float


class ModelRuntime:
    """Loads models in a background thread while exposing live/readiness separately."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._finished = threading.Event()
        self._started_ns: int | None = None
        self._finished_ns: int | None = None
        self._models: dict[str, Any] | None = None
        self._error: BaseException | None = None

    def start(self, loader: Callable[[], dict[str, Any]]) -> None:
        with self._lock:
            if self._started_ns is not None:
                return
            self._started_ns = time.perf_counter_ns()
        threading.Thread(target=self._load, args=(loader,), daemon=True,
                         name="model-loader").start()

    def _load(self, loader: Callable[[], dict[str, Any]]) -> None:
        try:
            models = loader()
            with self._lock:
                self._models = models
        except BaseException as exc:  # readiness must retain failures from the loader thread
            with self._lock:
                self._error = exc
        finally:
            with self._lock:
                self._finished_ns = time.perf_counter_ns()
            self._finished.set()

    def wait(self, timeout_seconds: float) -> dict[str, Any]:
        if not self._finished.wait(timeout_seconds):
            raise TimeoutError("model readiness timeout")
        with self._lock:
            if self._error is not None:
                raise RuntimeError("model loading failed") from self._error
            if self._models is None:
                raise RuntimeError("model runtime is unavailable")
            return self._models

    def snapshot(self) -> RuntimeSnapshot:
        with self._lock:
            started_ns = self._started_ns
            finished_ns = self._finished_ns
            has_models = self._models is not None
            has_error = self._error is not None
        if started_ns is None:
            return RuntimeSnapshot("starting", 0.0)
        end_ns = finished_ns if finished_ns is not None else time.perf_counter_ns()
        duration_ms = max(0.0, (end_ns - started_ns) / 1_000_000.0)
        if has_error:
            status = "error"
        elif has_models:
            status = "ready"
        else:
            status = "loading"
        return RuntimeSnapshot(status, duration_ms)
