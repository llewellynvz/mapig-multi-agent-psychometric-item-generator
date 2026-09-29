import pytest

from backend.agents.correlation_estimator import clear_embedding_cache


@pytest.fixture(autouse=True)
def _fresh_embedding_cache():
    # Tests mock the embeddings client with different vectors for the same
    # texts; a vector cached by one test must not leak into the next.
    clear_embedding_cache()
    yield
    clear_embedding_cache()
