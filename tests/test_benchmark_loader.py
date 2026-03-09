"""Tests for benchmark scale loader."""

import os
import json
import pytest
from pathlib import Path

# Set mock mode for tests
os.environ["APP_MODE"] = "mock"

from backend.evaluation.benchmark_loader import (
    load_benchmark_scales,
    save_benchmark_scales
)
from backend.evaluation.schemas import BenchmarkScale


def test_load_benchmark_scales_returns_five_scales():
    """Benchmark file contains 5 scales."""
    # Assumes benchmark_scales.json exists after Task 2
    scales = load_benchmark_scales()
    assert len(scales) == 5


def test_each_scale_has_minimum_items():
    """Each scale must have at least 5 items."""
    scales = load_benchmark_scales()
    for scale in scales:
        assert len(scale.items) >= 5, f"{scale.name} has fewer than 5 items"


def test_all_domains_represented():
    """All 5 domains must be present."""
    scales = load_benchmark_scales()
    domains = {scale.domain for scale in scales}
    expected = {"personality", "clinical", "social", "organizational", "attitudes"}
    assert domains == expected


def test_save_and_load_roundtrip(tmp_path):
    """Save and load produces identical scales."""
    original = [
        BenchmarkScale(
            name="Test Scale",
            author="Test Author",
            year=2020,
            domain="personality",
            citation="Test citation",
            items=["Item 1", "Item 2", "Item 3", "Item 4", "Item 5"],
            license="CC BY"
        )
    ]

    filepath = tmp_path / "test_scales.json"
    save_benchmark_scales(original, filepath)
    loaded = load_benchmark_scales(filepath)

    assert len(loaded) == 1
    assert loaded[0].name == "Test Scale"
    assert len(loaded[0].items) == 5


def test_benchmark_scales_json_exists_and_valid():
    """Benchmark scales JSON file exists and contains valid data."""
    filepath = Path("data/benchmarks/benchmark_scales.json")

    # File must exist
    assert filepath.exists(), "benchmark_scales.json not found in data/benchmarks/"

    # Must be valid JSON
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Must contain 5 scales
    assert len(data) == 5, f"Expected 5 scales, found {len(data)}"

    # Each scale must have required fields
    required_fields = {"name", "author", "year", "domain", "citation", "items", "license"}
    for scale in data:
        assert set(scale.keys()) == required_fields, f"Scale {scale.get('name')} missing required fields"
        assert len(scale["items"]) >= 5, f"Scale {scale.get('name')} has fewer than 5 items"
