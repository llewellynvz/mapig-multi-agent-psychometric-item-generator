import logging
import time
from contextlib import contextmanager
from typing import Any, Dict, Iterator, Optional

logger = logging.getLogger("lmaig")


@contextmanager
def step(step_name: str, state: Optional[Dict[str, Any]] = None) -> Iterator[None]:
    start = time.perf_counter()

    if state is None:
        logger.info("STEP_START %s", step_name)
    else:
        logger.info(
            "STEP_START %s thread_id=%s run_id=%s iteration=%s",
            step_name,
            state.get("thread_id"),
            state.get("run_id"),
            state.get("iteration"),
        )

    try:
        yield
    finally:
        dur = time.perf_counter() - start
        logger.info("STEP_END %s duration=%.3fs", step_name, dur)
