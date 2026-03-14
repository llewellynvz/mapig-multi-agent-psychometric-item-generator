"""Phase 9 Plan 01: Instrument searcher tests."""
import pytest
from unittest.mock import Mock, patch
import httpx

from backend.agents.instrument_searcher import (
    search_instruments,
    _get_hardcoded_defaults,
    _is_blocked_publisher,
)
from backend.schemas import ComparisonInstrument


def test_search_convergent_instrument():
    """Test that search_instruments returns convergent instrument with valid metadata."""
    with patch('backend.agents.instrument_searcher._search_perplexity_instrument') as mock_search:
        # Mock successful Perplexity search
        mock_convergent = ComparisonInstrument(
            name="Rosenberg Self-Esteem Scale",
            construct="self-esteem",
            source_citation="Rosenberg, M. (1965). Society and the adolescent self-image. Princeton, NJ: Princeton University Press.",
            publication_year=1965,
            sample_items_count=10,
            psychometric_properties="α = 0.88, test-retest reliability = 0.85",
            similarity_rationale="Directly measures self-esteem construct"
        )
        mock_discriminant = ComparisonInstrument(
            name="PHQ-9",
            construct="depression",
            source_citation="Kroenke, K., & Spitzer, R. L. (2002). The PHQ-9. Journal of General Internal Medicine, 16(9), 606-613.",
            publication_year=2002,
            sample_items_count=9,
            psychometric_properties="α = 0.89",
            similarity_rationale="Related to but distinct from self-esteem"
        )
        mock_search.side_effect = [mock_convergent, mock_discriminant]

        convergent, discriminant = search_instruments("self-esteem", "A person's overall subjective evaluation of their own worth")

        assert convergent.name == "Rosenberg Self-Esteem Scale"
        assert convergent.construct == "self-esteem"
        assert convergent.publication_year == 1965
        assert discriminant.name == "PHQ-9"
        assert discriminant.construct == "depression"


def test_hardcoded_defaults_coverage():
    """Test that hardcoded defaults cover all 5 psychological domains."""
    # Test personality domain
    conv, disc = _get_hardcoded_defaults("extraversion")
    assert conv.name is not None
    assert "personality" in conv.construct.lower() or "extraversion" in conv.construct.lower() or "NEO" in conv.name or "IPIP" in conv.name

    # Test clinical domain
    conv, disc = _get_hardcoded_defaults("depression")
    assert conv.name is not None
    assert "depression" in conv.construct.lower() or "PHQ" in conv.name

    # Test organizational domain
    conv, disc = _get_hardcoded_defaults("work engagement")
    assert conv.name is not None
    assert "engagement" in conv.construct.lower() or "work" in conv.construct.lower() or "UWES" in conv.name

    # Test social domain
    conv, disc = _get_hardcoded_defaults("loneliness")
    assert conv.name is not None
    assert "loneliness" in conv.construct.lower() or "UCLA" in conv.name

    # Test cognitive domain
    conv, disc = _get_hardcoded_defaults("need for cognition")
    assert conv.name is not None
    assert "cognition" in conv.construct.lower() or "cognitive" in conv.construct.lower()


def test_search_fallback_on_failure():
    """Test graceful fallback to defaults when Perplexity fails."""
    with patch('backend.agents.instrument_searcher._search_perplexity_instrument') as mock_search:
        # Mock timeout error
        mock_search.side_effect = httpx.TimeoutException("Connection timeout")

        convergent, discriminant = search_instruments("self-esteem", "A person's overall evaluation of their worth")

        # Should return valid instruments from defaults
        assert convergent.name is not None
        assert discriminant.name is not None
        assert len(convergent.source_citation) >= 5


def test_publisher_blocklist():
    """Test that publisher blocklist filters copyrighted instruments."""
    # Test blocked publishers
    assert _is_blocked_publisher("Available from pearson.com", "") is True
    assert _is_blocked_publisher("", "Purchase at parinc.com for $199") is True
    assert _is_blocked_publisher("Published by mhs.com", "") is True
    assert _is_blocked_publisher("", "Contact wpspublish.com") is True
    assert _is_blocked_publisher("Smith et al. (2020). Available from hogrefe.com", "") is True

    # Test non-blocked sources
    assert _is_blocked_publisher("Available at doi.org/10.1037/xyz", "") is False
    assert _is_blocked_publisher("Published in Journal of Personality", "Open access article") is False


def test_related_construct_discovery():
    """Test discriminant instrument search for related-but-distinct constructs."""
    with patch('backend.agents.instrument_searcher._search_perplexity_instrument') as mock_search:
        mock_convergent = ComparisonInstrument(
            name="RSES",
            construct="self-esteem",
            source_citation="Rosenberg (1965)",
            publication_year=1965,
            sample_items_count=10
        )
        mock_discriminant = ComparisonInstrument(
            name="SWLS",
            construct="life satisfaction",
            source_citation="Diener et al. (1985)",
            publication_year=1985,
            sample_items_count=5,
            similarity_rationale="Related to self-esteem but measures broader life satisfaction"
        )
        mock_search.side_effect = [mock_convergent, mock_discriminant]

        conv, disc = search_instruments("self-esteem", "Overall self-worth")

        # Discriminant should be related but distinct
        assert disc.construct != conv.construct
        assert disc.similarity_rationale is not None
