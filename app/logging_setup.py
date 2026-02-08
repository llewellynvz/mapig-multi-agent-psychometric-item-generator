import logging
import os
import sys
from typing import Optional


def configure_logging(level: Optional[int] = None) -> None:
    """
    Structured-ish logging that works locally and on Azure.
    Adds optional noise control for httpx/openai loggers.
    """

    # Allow env override: LOG_LEVEL=DEBUG/INFO/WARNING
    if level is None:
        env_level = os.getenv("LOG_LEVEL", "INFO").upper()
        level = getattr(logging, env_level, logging.INFO)

    root = logging.getLogger()
    if root.handlers:
        return  # Avoid duplicate handlers in reload environments

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    handler.setFormatter(formatter)

    root.addHandler(handler)
    root.setLevel(level)

    # Reduce spam unless explicitly debugging
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
