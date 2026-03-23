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

__all__ = []



