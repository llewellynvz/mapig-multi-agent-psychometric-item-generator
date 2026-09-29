"""Benchmark scale loader.

Loads and saves the curated benchmark scales in
data/benchmarks/benchmark_scales.json. That file is hand-curated (see
data/benchmarks/README.md); nothing here sources or parses scales from search
evidence. An earlier ``source_benchmark_scales`` / ``_parse_scale_from_evidence``
path ran a web search and then discarded the evidence in favour of hardcoded
scales; it had no callers and was removed so nothing implies the scales were
extracted from search results.
"""

import json
import logging
from pathlib import Path
from backend.evaluation.schemas import BenchmarkScale

logger = logging.getLogger(__name__)


# Anchored to the repo root so loading works whatever the working directory.
_DEFAULT_PATH = Path(__file__).resolve().parents[2] / "data" / "benchmarks" / "benchmark_scales.json"


def load_benchmark_scales(filepath: Path | None = None) -> list[BenchmarkScale]:
    """Load benchmark scales from JSON file.

    Args:
        filepath: Path to benchmark_scales.json
                  (default: data/benchmarks/benchmark_scales.json)

    Returns:
        List of BenchmarkScale objects

    Raises:
        FileNotFoundError: If benchmark scales file doesn't exist
    """
    if filepath is None:
        filepath = _DEFAULT_PATH

    if not filepath.exists():
        raise FileNotFoundError(f"Benchmark scales file not found: {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    return [BenchmarkScale(**scale) for scale in data]


def save_benchmark_scales(scales: list[BenchmarkScale], filepath: Path | None = None):
    """Save benchmark scales to JSON file.

    Args:
        scales: List of BenchmarkScale objects
        filepath: Path to save (default: data/benchmarks/benchmark_scales.json)
    """
    if filepath is None:
        filepath = _DEFAULT_PATH

    filepath.parent.mkdir(parents=True, exist_ok=True)

    data = [scale.model_dump() for scale in scales]

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    logger.info(f"Saved {len(scales)} benchmark scales to {filepath}")
