"""Test suite for Web Surfer agent enhancements.

Task #4: Theoretical model discovery tests.
"""

import os
import pytest

os.environ["APP_MODE"] = "mock"


def test_synthesize_theoretical_query():
    """Task #4: Query synthesis includes theoretical discovery guidance."""
    from backend.agents.web_surfer import _synthesize_theoretical_query
    from backend.schemas import UserRequest

    # Arrange: Create test request
    request = UserRequest(
        construct_name="Flourishing",
        construct_definition="A state of positive mental health characterized by emotional, psychological, and social well-being",
        target_population="General adult population",
        response_scale="1-5 Likert",
        item_count=10,
        construct_exclusions="Not merely the absence of mental illness"
    )

    # Act: Synthesize query
    query = _synthesize_theoretical_query(request, "Boundary exclusions: Not merely the absence of mental illness.\n", "")

    # Assert: Query includes theoretical discovery guidance
    assert "theoretical definition" in query.lower()
    assert "conceptual model" in query.lower()
    assert "Flourishing" in query
    assert "positive mental health" in query
    assert "authoritative academic definitions" in query.lower()
    assert "theoretical frameworks" in query.lower()
    assert "subcomponents, dimensions, or facets" in query.lower()
    assert "differs from similar or neighboring constructs" in query.lower()
    assert "measurement instruments" in query.lower()
    assert "do not quote items" in query.lower()


def test_process_perplexity_response_with_structured_evidence():
    """Task #4: Process structured evidence from Perplexity LLM response."""
    from backend.agents.web_surfer import _process_perplexity_response

    # Arrange: Mock Perplexity response with structured evidence
    mock_response = {
        "choices": [{
            "message": {
                "content": """Here is the evidence I found:

{
  "evidence": [
    {
      "source_id": "web:keyes2002",
      "title": "Keyes (2002) - Mental Health Continuum",
      "quote": "Flourishing is characterized by high levels of emotional, psychological, and social well-being.",
      "url_or_docref": "https://doi.org/10.1037/0022-006X.70.3.674",
      "evidence_type": "theoretical_definition",
      "authors": "Keyes, C. L. M.",
      "theoretical_model": "Two-Continua Model of Mental Health",
      "dimensions": ["emotional well-being", "psychological well-being", "social well-being"]
    }
  ]
}"""
            }
        }]
    }

    # Act: Process response
    evidence = _process_perplexity_response(mock_response)

    # Assert: Structured evidence extracted correctly
    assert len(evidence) == 1
    assert evidence[0].source_id == "web:keyes2002"
    assert evidence[0].evidence_type == "theoretical_definition"
    assert evidence[0].authors == "Keyes, C. L. M."
    assert evidence[0].theoretical_model == "Two-Continua Model of Mental Health"
    assert evidence[0].dimensions == ["emotional well-being", "psychological well-being", "social well-being"]


def test_process_perplexity_response_fallback():
    """Task #4: Fallback to search_results if LLM doesn't return structured JSON."""
    from backend.agents.web_surfer import _process_perplexity_response

    # Arrange: Mock response without structured JSON (only search_results)
    mock_response = {
        "choices": [{
            "message": {
                "content": "Here are some relevant sources about flourishing, but no structured JSON."
            }
        }],
        "search_results": [
            {
                "url": "https://doi.org/10.1037/example",
                "title": "Flourishing Research",
                "snippet": "A study on flourishing and well-being in adults."
            }
        ]
    }

    # Act: Process response (should fallback)
    evidence = _process_perplexity_response(mock_response)

    # Assert: Fallback to search_results
    assert len(evidence) == 1
    assert evidence[0].title == "Flourishing Research"
    assert evidence[0].url_or_docref == "https://doi.org/10.1037/example"
    # Fallback mode doesn't have theoretical metadata
    assert evidence[0].evidence_type is None
    assert evidence[0].authors is None
    assert evidence[0].theoretical_model is None
    assert evidence[0].dimensions is None


def test_process_perplexity_response_multiple_evidence_types():
    """Task #4: Process multiple evidence chunks with different types."""
    from backend.agents.web_surfer import _process_perplexity_response

    # Arrange: Mock response with mixed evidence types
    mock_response = {
        "choices": [{
            "message": {
                "content": """{
  "evidence": [
    {
      "source_id": "web:def1",
      "title": "Theoretical Definition",
      "quote": "Definition quote",
      "url_or_docref": "https://example.com/1",
      "evidence_type": "theoretical_definition",
      "authors": "Author A"
    },
    {
      "source_id": "web:dim1",
      "title": "Dimensions Paper",
      "quote": "Dimensions quote",
      "url_or_docref": "https://example.com/2",
      "evidence_type": "dimensions",
      "dimensions": ["dim1", "dim2", "dim3"]
    },
    {
      "source_id": "web:measure1",
      "title": "Measurement Study",
      "quote": "Measurement quote",
      "url_or_docref": "https://example.com/3",
      "evidence_type": "measurement_precedent"
    },
    {
      "source_id": "web:boundary1",
      "title": "Boundary Conditions",
      "quote": "Boundary quote",
      "url_or_docref": "https://example.com/4",
      "evidence_type": "boundary_conditions"
    }
  ]
}"""
            }
        }]
    }

    # Act: Process response
    evidence = _process_perplexity_response(mock_response)

    # Assert: All evidence types processed correctly
    assert len(evidence) == 4
    assert evidence[0].evidence_type == "theoretical_definition"
    assert evidence[1].evidence_type == "dimensions"
    assert evidence[2].evidence_type == "measurement_precedent"
    assert evidence[3].evidence_type == "boundary_conditions"

    # Assert: Type-specific metadata preserved
    assert evidence[0].authors == "Author A"
    assert evidence[1].dimensions == ["dim1", "dim2", "dim3"]


def test_process_perplexity_response_malformed_json():
    """Task #4: Gracefully handle malformed JSON in LLM response."""
    from backend.agents.web_surfer import _process_perplexity_response

    # Arrange: Mock response with malformed JSON
    mock_response = {
        "choices": [{
            "message": {
                "content": '{"evidence": [{"incomplete": true'  # Malformed JSON
            }
        }],
        "search_results": [
            {
                "url": "https://example.com",
                "title": "Fallback Source",
                "snippet": "Fallback content"
            }
        ]
    }

    # Act: Process response (should fallback gracefully)
    evidence = _process_perplexity_response(mock_response)

    # Assert: Falls back to search_results without crashing
    assert len(evidence) == 1
    assert evidence[0].title == "Fallback Source"
