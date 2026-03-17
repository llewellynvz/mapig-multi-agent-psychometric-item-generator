"""Plagiarism detection using OpenAI embeddings and cosine similarity.

Phase 9 Plan 01: Semantic similarity detection to flag potential item plagiarism
from published instruments. Uses text-embedding-3-small (same model as correlation
estimator) instead of local sentence-transformers to avoid PyTorch dependency
(~2 GB) that exceeds Vercel's 500 MB Lambda limit.
"""
from __future__ import annotations

import logging
from typing import Optional

import numpy as np
from openai import OpenAI

from backend.settings import settings

log = logging.getLogger("lmaig.similarity_calculator")


class PlagiarismDetector:
    """Detect potential plagiarism using semantic similarity.

    Uses OpenAI text-embedding-3-small to encode items into embeddings,
    then computes cosine similarity to flag items exceeding the configured
    threshold.
    """

    def __init__(self, threshold: Optional[float] = None):
        self.threshold = threshold if threshold is not None else settings.PLAGIARISM_SIMILARITY_THRESHOLD

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
        """
        if not generated_items or not published_items:
            return {}

        log.info(
            "PLAGIARISM_DETECTOR encoding items generated=%d published=%d",
            len(generated_items), len(published_items),
        )

        log.info(
            "PLAGIARISM_DETECTOR creating OpenAI client api_key_set=%s base_url=%s",
            bool(settings.OPENAI_API_KEY),
            settings.OPENAI_BASE_URL or "default",
        )
        client = OpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL or "https://api.openai.com/v1",
        )

        # Embed all items in a single batch
        all_texts = generated_items + published_items
        resp = client.embeddings.create(input=all_texts, model="text-embedding-3-small")
        all_vecs = np.array([d.embedding for d in resp.data])

        # Split back into generated vs published
        gen_vecs = all_vecs[: len(generated_items)]
        pub_vecs = all_vecs[len(generated_items) :]

        # L2-normalize
        gen_norms = np.linalg.norm(gen_vecs, axis=1, keepdims=True)
        gen_norms = np.where(gen_norms == 0, 1, gen_norms)
        gen_normed = gen_vecs / gen_norms

        pub_norms = np.linalg.norm(pub_vecs, axis=1, keepdims=True)
        pub_norms = np.where(pub_norms == 0, 1, pub_norms)
        pub_normed = pub_vecs / pub_norms

        # Cosine similarity matrix: (num_generated, num_published)
        similarities = np.clip(gen_normed @ pub_normed.T, -1.0, 1.0)

        # Find flagged items
        flagged: dict[int, str] = {}
        for i in range(len(generated_items)):
            max_sim = float(similarities[i].max())
            if max_sim >= self.threshold:
                warning = f"Potential similarity to {instrument_name} item (r = {max_sim:.2f})"
                flagged[i] = warning
                log.info("PLAGIARISM_DETECTOR flagged item_index=%d similarity=%.3f", i, max_sim)

        log.info("PLAGIARISM_DETECTOR done flagged=%d/%d", len(flagged), len(generated_items))
        return flagged


_detector: Optional[PlagiarismDetector] = None


def get_plagiarism_detector() -> PlagiarismDetector:
    """Get or create singleton PlagiarismDetector instance."""
    global _detector
    if _detector is None:
        _detector = PlagiarismDetector()
    return _detector
