from __future__ import annotations

from functools import lru_cache
from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


@lru_cache(maxsize=1)
def _load_shared_prompt() -> str:
    """Load and cache the shared system prompt.

    Cached to avoid repeated file I/O across multiple agent invocations.
    Returns empty string if _shared.md doesn't exist.
    """
    shared_path = PROMPTS_DIR / "_shared.md"
    if shared_path.exists():
        return shared_path.read_text(encoding="utf-8").strip()
    return ""


@lru_cache(maxsize=20)
def load_prompt(prompt_filename: str) -> str:
    """Load an agent prompt, optionally prepending a shared system prompt.

    Both the shared prompt (_shared.md) and individual agent prompts are cached
    in memory to reduce file I/O and improve performance.

    Args:
        prompt_filename: Name of agent-specific prompt file (e.g., "item_writer.md")

    Returns:
        Combined prompt with shared prefix (if exists) + agent-specific prompt

    Raises:
        FileNotFoundError: If agent prompt file doesn't exist
    """
    agent_path = PROMPTS_DIR / prompt_filename

    if not agent_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {agent_path}")

    shared = _load_shared_prompt()
    agent = agent_path.read_text(encoding="utf-8").strip()

    return f"{shared}\n\n{agent}" if shared else agent
