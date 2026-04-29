import warnings

# Suppress PydanticSerializationUnexpectedValue warnings from the OpenAI SDK.
# The OpenAI SDK's ParsedResponse has a 21-variant discriminated union that
# triggers Pydantic v2 serialization warnings when model_dump() is called.
# Data parses correctly — warnings are cosmetic noise.
# See: https://github.com/openai/openai-python/issues/2872
#      https://github.com/langchain-ai/langchain/issues/35538
warnings.filterwarnings(
    "ignore",
    message="(?s).*Pydantic serializer warnings.*",
    category=UserWarning,
)
warnings.filterwarnings(
    "ignore",
    message=".*serialized value may not be as expected.*",
    category=UserWarning,
)

# Suppress joblib's "operate in serial mode" warning. Vercel serverless has no
# shared-memory parallelism, so joblib (transitively imported by factor-analyzer
# via scikit-learn) emits this warning every cold start. Harmless — for our
# small N item batches, single-threaded is fine. If we ever scale to large N,
# revisit.
warnings.filterwarnings(
    "ignore",
    message=".*joblib will operate in serial mode.*",
    category=UserWarning,
)

# Suppress factor-analyzer's "No rotation" warning. Fires when n_factors==1
# (the unidimensional case is correct — no rotation needed). Cosmetic noise.
warnings.filterwarnings(
    "ignore",
    message=".*No rotation will be performed when the number of factors equals 1.*",
    category=UserWarning,
)

# Suppress Pydantic v1 / Python 3.14+ deprecation warning. Triggered when
# langchain_core imports pydantic.v1 for backward compatibility. Upstream
# issue we can't fix; documented in CLAUDE.md as harmless.
warnings.filterwarnings(
    "ignore",
    message=".*Core Pydantic V1 functionality isn't compatible with Python 3.14.*",
    category=UserWarning,
)

__all__ = []



