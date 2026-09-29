import logging
import threading
import time
from collections import deque
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Iterator, Optional

logger = logging.getLogger("lmaig")

# Performance tracking. Steps run on several to_thread workers at once, so
# updates take a lock; each step keeps only its most recent durations so a
# long-lived server doesn't grow the log without bound.
_PERFORMANCE_WINDOW = 500
_performance_log: Dict[str, deque] = {}
_performance_lock = threading.Lock()


def emit_log_event(
    level: str,
    source: str,
    message: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create a log event dictionary for SSE streaming.

    Args:
        level: "info", "warning", or "error"
        source: Agent name or step name
        message: Log message
        metadata: Optional metadata (tokens, duration, etc.)

    Returns:
        Dictionary representing a log event
    """
    return {
        "type": "log",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": level,
        "source": source,
        "message": message,
        "metadata": metadata or {},
    }


@contextmanager
def step(step_name: str, state: Optional[Dict[str, Any]] = None) -> Iterator[None]:
    start = time.perf_counter()
    iteration = state.get("iteration", 0) if state else 0

    if state is None:
        logger.info("STEP_START %s", step_name)
    else:
        logger.info(
            "STEP_START %s thread_id=%s run_id=%s iteration=%s",
            step_name,
            state.get("thread_id"),
            state.get("run_id"),
            iteration,
        )

    try:
        yield
    finally:
        dur = time.perf_counter() - start
        logger.info("STEP_END %s duration=%.3fs iteration=%s", step_name, dur, iteration)
        
        # Track performance for analysis
        key = f"{step_name}_iter{iteration}"
        with _performance_lock:
            _performance_log.setdefault(key, deque(maxlen=_PERFORMANCE_WINDOW)).append(dur)
        
        # Log if step is taking unusually long (>10s)
        if dur > 10.0:
            logger.warning("SLOW_STEP %s took %.3fs (iteration=%s)", step_name, dur, iteration)


def get_performance_summary() -> Dict[str, Dict[str, float]]:
    """Get performance statistics for all steps."""
    summary = {}
    with _performance_lock:
        snapshot = {key: list(durations) for key, durations in _performance_log.items()}
    for key, durations in snapshot.items():
        if durations:
            summary[key] = {
                "count": len(durations),
                "total": sum(durations),
                "avg": sum(durations) / len(durations),
                "min": min(durations),
                "max": max(durations),
            }
    return summary


def reset_performance_log():
    """Clear performance tracking (useful for testing)."""
    with _performance_lock:
        _performance_log.clear()
