#!/usr/bin/env python3
"""Test that Settings handles whitespace in environment variables correctly."""

import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

def test_whitespace_handling():
    """Test that APP_MODE with trailing newline is handled correctly."""
    # Set environment variable with trailing newline (simulating Vercel issue)
    os.environ['APP_MODE'] = 'claude\n'
    os.environ['CLAUDE_API_KEY'] = 'test-key-with-space '
    os.environ['SEARCH_PROVIDER'] = ' perplexity'  # Leading space

    # Import and instantiate settings
    from backend.settings import Settings

    # Create fresh settings instance (not the singleton)
    settings = Settings()

    # Verify whitespace was stripped
    assert settings.APP_MODE == 'claude', f"Expected 'claude', got {repr(settings.APP_MODE)}"
    assert settings.CLAUDE_API_KEY == 'test-key-with-space', f"Expected 'test-key-with-space', got {repr(settings.CLAUDE_API_KEY)}"
    assert settings.SEARCH_PROVIDER == 'perplexity', f"Expected 'perplexity', got {repr(settings.SEARCH_PROVIDER)}"

    print("[PASS] All whitespace handling tests passed!")
    print(f"   APP_MODE: {repr(settings.APP_MODE)} (stripped trailing newline)")
    print(f"   CLAUDE_API_KEY: {repr(settings.CLAUDE_API_KEY)} (stripped trailing space)")
    print(f"   SEARCH_PROVIDER: {repr(settings.SEARCH_PROVIDER)} (stripped leading space)")

    # Clean up
    del os.environ['APP_MODE']
    del os.environ['CLAUDE_API_KEY']
    del os.environ['SEARCH_PROVIDER']

if __name__ == '__main__':
    try:
        test_whitespace_handling()
    except Exception as e:
        print(f"[FAIL] Test failed: {e}")
        sys.exit(1)
