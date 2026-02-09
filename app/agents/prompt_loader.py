from __future__ import annotations

from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"

def load_prompt(prompt_filename: str) -> str:
    """Load an agent prompt, optionally prepending a shared system prompt."""
    shared_path = PROMPTS_DIR / "_shared.md"
    agent_path = PROMPTS_DIR / prompt_filename

    if not agent_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {agent_path}")

    shared = shared_path.read_text(encoding="utf-8") if shared_path.exists() else ""
    agent = agent_path.read_text(encoding="utf-8")

    shared = shared.strip()
    agent = agent.strip()
    return f"{shared}\n\n{agent}" if shared else agent
