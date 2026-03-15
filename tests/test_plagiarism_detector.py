"""Phase 9 Plan 01: Plagiarism detector tests.

Uses mock OpenAI embeddings to avoid API calls in tests.
"""
import pytest
from unittest.mock import patch, MagicMock
import numpy as np

from backend.analytics.similarity_calculator import PlagiarismDetector, get_plagiarism_detector


def _mock_embeddings(texts, *, similar_pairs=None):
    """Create mock OpenAI embeddings response.

    Args:
        texts: List of input texts
        similar_pairs: List of (i, j) tuples where texts[i] and texts[j] should
                      have high cosine similarity. Indices are into the combined
                      texts list. If None, generates random vectors (low similarity).
    """
    dim = 64
    rng = np.random.RandomState(42)
    # Start with random orthogonal-ish vectors
    vecs = rng.randn(len(texts), dim)

    if similar_pairs:
        for i, j in similar_pairs:
            if i < len(vecs) and j < len(vecs):
                # Make j a near-copy of i (tiny noise → cosine ~0.99)
                vecs[j] = vecs[i] + rng.randn(dim) * 0.05

    # Normalize so cosine similarity = dot product
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1, norms)
    vecs = vecs / norms

    mock_resp = MagicMock()
    mock_resp.data = []
    for vec in vecs:
        item = MagicMock()
        item.embedding = vec.tolist()
        mock_resp.data.append(item)
    return mock_resp


@patch("backend.analytics.similarity_calculator.OpenAI")
def test_similarity_threshold(MockOpenAI):
    """Test that items exceeding similarity threshold are flagged."""
    detector = PlagiarismDetector(threshold=0.60)

    generated_items = [
        "I feel confident in my abilities",
        "The weather is sunny today"
    ]
    published_items = [
        "I believe in my capabilities",
        "It is a beautiful day outside"
    ]

    # Mock: make generated[0] similar to published[0], generated[1] similar to published[1]
    mock_client = MagicMock()
    MockOpenAI.return_value = mock_client
    mock_client.embeddings.create.return_value = _mock_embeddings(
        generated_items + published_items,
        similar_pairs=[(0, 2), (1, 3)]  # gen[0]~pub[0], gen[1]~pub[1]
    )

    flagged = detector.detect_plagiarism(generated_items, published_items, "Test Scale")

    assert len(flagged) > 0
    assert "Test Scale" in list(flagged.values())[0]
    assert "r =" in list(flagged.values())[0]

    import re
    match = re.search(r'r = (\d\.\d+)', list(flagged.values())[0])
    assert match is not None
    correlation = float(match.group(1))
    assert correlation >= 0.60


@patch("backend.analytics.similarity_calculator.OpenAI")
def test_no_plagiarism_below_threshold(MockOpenAI):
    """Test that items below threshold are not flagged."""
    detector = PlagiarismDetector(threshold=0.85)

    generated_items = ["I enjoy reading books"]
    published_items = ["Mathematics is challenging"]

    mock_client = MagicMock()
    MockOpenAI.return_value = mock_client
    # No similar_pairs → random orthogonal vectors → low similarity
    mock_client.embeddings.create.return_value = _mock_embeddings(
        generated_items + published_items
    )

    flagged = detector.detect_plagiarism(generated_items, published_items, "Different Scale")
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


@patch("backend.analytics.similarity_calculator.OpenAI")
def test_configurable_threshold(MockOpenAI):
    """Test that threshold is configurable."""
    detector_low = PlagiarismDetector(threshold=0.5)

    generated = ["I like pizza"]
    published = ["I enjoy pizza"]

    mock_client = MagicMock()
    MockOpenAI.return_value = mock_client
    mock_client.embeddings.create.return_value = _mock_embeddings(
        generated + published,
        similar_pairs=[(0, 1)]
    )

    flagged_low = detector_low.detect_plagiarism(generated, published, "Scale")
    assert 0 in flagged_low


@patch("backend.analytics.similarity_calculator.OpenAI")
def test_warning_message_format(MockOpenAI):
    """Test that warning message follows specified format."""
    detector = PlagiarismDetector(threshold=0.60)

    generated = ["I feel confident in my abilities"]
    published = ["I believe in my capabilities"]

    mock_client = MagicMock()
    MockOpenAI.return_value = mock_client
    mock_client.embeddings.create.return_value = _mock_embeddings(
        generated + published,
        similar_pairs=[(0, 1)]
    )

    flagged = detector.detect_plagiarism(generated, published, "Rosenberg Self-Esteem Scale")

    assert len(flagged) > 0
    assert "Rosenberg Self-Esteem Scale" in list(flagged.values())[0]

    import re
    assert re.search(r'r = \d\.\d{2}', list(flagged.values())[0]) is not None


def test_singleton_factory():
    """Test that get_plagiarism_detector returns singleton instance."""
    # Reset singleton for clean test
    import backend.analytics.similarity_calculator as mod
    mod._detector = None

    detector1 = get_plagiarism_detector()
    detector2 = get_plagiarism_detector()
    assert detector1 is detector2
