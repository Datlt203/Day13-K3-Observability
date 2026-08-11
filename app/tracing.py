from __future__ import annotations

import json
import os
import threading
import time
import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from structlog.contextvars import bind_contextvars, get_contextvars

try:
    from langfuse import get_client, observe

    LANGFUSE_SDK_AVAILABLE = True
except ImportError:  # pragma: no cover - chỉ dùng khi chưa cài requirements
    LANGFUSE_SDK_AVAILABLE = False

    def observe(*args: Any, **kwargs: Any):
        def decorator(func):
            return func

        return decorator

    class _DummyClient:
        def update_current_trace(self, **kwargs: Any) -> None:
            return None

        def update_current_generation(self, **kwargs: Any) -> None:
            return None

    def get_client():
        return _DummyClient()


def get_langfuse_client():
    return get_client()


def tracing_enabled() -> bool:
    return LANGFUSE_SDK_AVAILABLE and bool(
        os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY")
    )


LOCAL_TRACE_PATH = Path(os.getenv("LOCAL_TRACE_PATH", "data/traces.jsonl"))
_TRACE_FILE_LOCK = threading.Lock()
_CURRENT_LOCAL_TRACE: ContextVar["LocalTrace | None"] = ContextVar(
    "current_local_trace", default=None
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class LocalTrace:
    """A privacy-safe trace journal used when a Langfuse project is unavailable.

    It is deliberately a separate, explicitly labelled fallback; it does not
    claim that a managed Langfuse prompt/version was fetched.  This keeps the
    local lab runnable and preserves the Metrics -> Traces -> Logs workflow.
    """

    def __init__(self, *, metadata: dict[str, Any]) -> None:
        context = get_contextvars()
        self.trace_id = f"trace-{uuid.uuid4().hex[:16]}"
        self.correlation_id = context.get("correlation_id")
        self.started_at = _utc_now()
        self._started_perf = time.perf_counter()
        self.metadata = metadata
        self.spans: list[dict[str, Any]] = []
        self.error_type: str | None = None
        self._finished = False

    @contextmanager
    def span(self, name: str, span_type: str, metadata: dict[str, Any] | None = None):
        started_at = _utc_now()
        started_perf = time.perf_counter()
        span: dict[str, Any] = {
            "name": name,
            "type": span_type,
            "started_at": started_at,
            "metadata": metadata or {},
        }
        try:
            yield span
        except Exception as exc:
            span["error_type"] = type(exc).__name__
            raise
        finally:
            span["ended_at"] = _utc_now()
            span["latency_ms"] = int((time.perf_counter() - started_perf) * 1000)
            self.spans.append(span)

    def finish(self, *, output: dict[str, Any] | None = None, error: Exception | None = None) -> None:
        if self._finished:
            return
        self._finished = True
        if error is not None:
            self.error_type = type(error).__name__
        record = {
            "trace_id": self.trace_id,
            "correlation_id": self.correlation_id,
            "started_at": self.started_at,
            "ended_at": _utc_now(),
            "latency_ms": int((time.perf_counter() - self._started_perf) * 1000),
            "metadata": self.metadata,
            "spans": self.spans,
            "output": output or {},
            "error_type": self.error_type,
            "source": "local-trace-journal",
        }
        LOCAL_TRACE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with _TRACE_FILE_LOCK, LOCAL_TRACE_PATH.open("a", encoding="utf-8") as file:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")


@contextmanager
def capture_local_trace(*, metadata: dict[str, Any]):
    """Record a complete local trace and bind its ID into structured logs."""
    trace = LocalTrace(metadata=metadata)
    token = _CURRENT_LOCAL_TRACE.set(trace)
    bind_contextvars(trace_id=trace.trace_id)
    error: Exception | None = None
    try:
        yield trace
    except Exception as exc:
        error = exc
        raise
    finally:
        trace.finish(error=error)
        _CURRENT_LOCAL_TRACE.reset(token)


def current_local_trace() -> LocalTrace | None:
    return _CURRENT_LOCAL_TRACE.get()
