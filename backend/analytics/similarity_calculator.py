"""Plagiarism detection using sentence transformers and cosine similarity.

Phase 9 Plan 01: Semantic similarity detection to flag potential item plagiarism
from published instruments using all-mpnet-base-v2 embeddings.
"""
from __future__ import annotations

import logging
from typing import Optional

from backend.settings import settings

log = logging.getLogger("lmaig.similarity_calculator")

# Lazy imports to avoid cold start penalty
_sentence_transformers_loaded = False
_SentenceTransformer = None
_cosine_similarity = None


def _ensure_imports():
    """Lazy-load sentence-transformers dependencies."""
    global _sentence_transformers_loaded, _SentenceTransformer, _cosine_similarity

    if _sentence_transformers_loaded:
        return

    try:
        from sentence_transformers import SentenceTransformer
        from sklearn.metrics.pairwise import cosine_similarity

        _SentenceTransformer = SentenceTransformer
        _cosine_similarity = cosine_similarity
        _sentence_transformers_loaded = True
        log.info("SIMILARITY_CALCULATOR lazy imports loaded")
    except ImportError as e:
        log.error("SIMILARITY_CALCULATOR import failed: %s", e)
        raise


class PlagiarismDetector:
    """Detect potential plagiarism using semantic similarity.

    Uses sentence-transformers (all-mpnet-base-v2) to encode items into
    768-dimensional embeddings, then computes cosine similarity to flag
    items exceeding the configured threshold.
    """

    def __init__(self, threshold: Optional[float] = None):
        """Initialize plagiarism detector.

        Args:
            threshold: Similarity threshold (0-1). Defaults to settings.PLAGIARISM_SIMILARITY_THRESHOLD.
        """
        self.threshold = threshold if threshold is not None else settings.PLAGIARISM_SIMILARITY_THRESHOLD
        self._model = None

    def _get_model(self):
        """Lazy-load SentenceTransformer model."""
        if self._model is None:
            _ensure_imports()
            log.info("PLAGIARISM_DETECTOR loading model all-mpnet-base-v2")
            self._model = _SentenceTransformer('all-mpnet-base-v2')
        return self._model

    def detect_plagiarism(
        self,
        generated_items: list[str],
        published_items: list[str],
        instrument_name: str
    ) -> dict[int, str]:
        """Detect potential plagiarism between generated and published items.

        Args:
            generated_items: List of generated item texts to check
            published_items: List of published item texts to compare against
            instrument_name: Name of the published instrument for warning messages

        Returns:
            Dict mapping flagged item indices to warning messages.
            Format: "Potential similarity to {instrument_name} item (r = {max_similarity:.2f})"
        """
        # Handle empty inputs
        if not generated_items or not published_items:
            return {}

        _ensure_imports()
        model = self._get_model()

        # Encode all items
        log.info("PLAGIARISM_DETECTOR encoding items generated=%d published=%d", len(generated_items), len(published_items))
        generated_embeddings = model.encode(generated_items)
        published_embeddings = model.encode(published_items)

        # Compute pairwise cosine similarities
        # Shape: (num_generated, num_published)
        similarities = _cosine_similarity(generated_embeddings, published_embeddings)

        # Find flagged items
        flagged = {}
        for i, item_similarities in enumerate(similarities):
            max_similarity = float(item_similarities.max())

            if max_similarity >= self.threshold:
                warning = f"Potential similarity to {instrument_name} item (r = {max_similarity:.2f})"
                flagged[i] = warning
                log.info("PLAGIARISM_DETECTOR flagged item_index=%d similarity=%.3f", i, max_similarity)

        log.info("PLAGIARISM_DETECTOR done flagged=%d/%d", len(flagged), len(generated_items))
        return flagged


# Singleton instance
_detector: Optional[PlagiarismDetector] = None


def get_plagiarism_detector() -> PlagiarismDetector:
    """Get or create singleton PlagiarismDetector instance.

    Returns:
        Shared PlagiarismDetector instance
    """
    global _detector
    if _detector is None:
        _detector = PlagiarismDetector()
    return _detector
