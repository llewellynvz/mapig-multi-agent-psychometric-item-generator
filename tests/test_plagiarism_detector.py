"""Phase 9 Plan 01: Plagiarism detector tests."""
import pytest

from backend.analytics.similarity_calculator import PlagiarismDetector, get_plagiarism_detector


def test_similarity_threshold():
    """Test that items exceeding similarity threshold are flagged."""
    # Use a lower threshold since paraphrased items typically have r=0.6-0.8
    detector = PlagiarismDetector(threshold=0.60)

    generated_items = [
        "I feel confident in my abilities",
        "The weather is sunny today"
    ]

    published_items = [
        "I believe in my capabilities",  # Similar to first generated item
        "It is a beautiful day outside"   # Similar to second generated item
    ]

    instrument_name = "Test Scale"

    flagged = detector.detect_plagiarism(generated_items, published_items, instrument_name)

    # At least one item should be flagged (semantically similar)
    assert len(flagged) > 0
    assert "Test Scale" in list(flagged.values())[0]
    assert "r =" in list(flagged.values())[0]

    # Extract correlation value from message
    import re
    match = re.search(r'r = (0\.\d+)', list(flagged.values())[0])
    assert match is not None
    correlation = float(match.group(1))
    assert correlation >= 0.60


def test_no_plagiarism_below_threshold():
    """Test that items below threshold are not flagged."""
    # Use a high threshold - unrelated items should have r < 0.3
    detector = PlagiarismDetector(threshold=0.85)

    generated_items = [
        "I enjoy reading books"
    ]

    published_items = [
        "Mathematics is challenging"  # Semantically unrelated
    ]

    instrument_name = "Different Scale"

    flagged = detector.detect_plagiarism(generated_items, published_items, instrument_name)

    # No items should be flagged (unrelated items have low similarity)
    assert len(flagged) == 0


def test_empty_generated_items():
    """Test graceful handling of empty generated items list."""
    detector = PlagiarismDetector()

    flagged = detector.detect_plagiarism([], ["Some published item"], "Test Scale")

    assert flagged == {}


def test_empty_published_items():
    """Test graceful handling of empty published items list."""
    detector = PlagiarismDetector()

    flagged = detector.detect_plagiarism(["Some generated item"], [], "Test Scale")

    assert flagged == {}


def test_configurable_threshold():
    """Test that threshold is configurable."""
    # Lower threshold should flag more items
    detector_low = PlagiarismDetector(threshold=0.5)

    generated = ["I like pizza"]
    published = ["I enjoy pizza"]

    flagged_low = detector_low.detect_plagiarism(generated, published, "Scale")

    # Should flag with low threshold
    assert 0 in flagged_low


def test_warning_message_format():
    """Test that warning message follows specified format."""
    # Use lower threshold to ensure flagging
    detector = PlagiarismDetector(threshold=0.60)

    generated = ["I feel confident in my abilities"]
    published = ["I believe in my capabilities"]

    flagged = detector.detect_plagiarism(generated, published, "Rosenberg Self-Esteem Scale")

    # Should have at least one flagged item
    assert len(flagged) > 0

    # Should contain instrument name
    assert "Rosenberg Self-Esteem Scale" in list(flagged.values())[0]

    # Should contain correlation value in format "r = X.XX"
    import re
    assert re.search(r'r = \d\.\d{2}', list(flagged.values())[0]) is not None


def test_singleton_factory():
    """Test that get_plagiarism_detector returns singleton instance."""
    detector1 = get_plagiarism_detector()
    detector2 = get_plagiarism_detector()

    assert detector1 is detector2
