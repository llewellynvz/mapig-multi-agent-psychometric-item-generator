"""Test validator handles None parsed response gracefully."""

import pytest
from unittest.mock import MagicMock, patch

from backend.agents.validator import validate_items
from backend.schemas import DraftItem, UserRequest


def test_validator_handles_none_parsed_response():
    """Test that validator raises informative error when parsing fails."""

    # Mock response with None parsed (simulating parse failure)
    mock_response = {"parsed": None, "raw": MagicMock()}

    # Patch settings.APP_MODE to bypass mock mode
    with patch("backend.agents.validator.settings.APP_MODE", "claude"):
        # Patch load_prompt to avoid file I/O
        with patch("backend.agents.validator.load_prompt") as mock_prompt:
            mock_prompt.return_value = "Test prompt"

            # Patch get_chat_model_for_agent
            with patch(
                "backend.agents.validator.get_chat_model_for_agent"
            ) as mock_get_model:
                # Setup mock chain
                mock_model = MagicMock()
                mock_model.model_name = "claude-sonnet-4-5"
                mock_runnable = MagicMock()
                mock_runnable.invoke.return_value = mock_response
                mock_model.with_structured_output.return_value = mock_runnable
                mock_get_model.return_value = mock_model

                # Patch _use_smart_validation
                with patch(
                    "backend.agents.validator._use_smart_validation", return_value=False
                ):
                    # Create test data
                    request = UserRequest(
                        construct_name="Test Construct",
                        construct_definition="Test definition for validation testing purposes",
                        target_population="Adult test participants",
                        response_scale="5-point Likert",
                        model_provider="claude",
                    )
                    items = [
                        DraftItem(
                            item_text="Test item 1",
                            construct_name="Test Construct",
                            rationale="This item tests the construct",
                        ),
                        DraftItem(
                            item_text="Test item 2",
                            construct_name="Test Construct",
                            rationale="This item also tests the construct",
                        ),
                    ]

                    # Should raise RuntimeError — fallback parse also fails on MagicMock content
                    with pytest.raises(
                        RuntimeError,
                        match="Validation agent failed.*could not extract JSON",
                    ):
                        validate_items(request, items, attempt=1)


def test_validator_handles_none_fallback_response():
    """Test that validator handles None in fallback path (no parsed/raw dict)."""

    # Mock direct None response (fallback path)
    mock_response = None

    # Patch settings.APP_MODE to bypass mock mode
    with patch("backend.agents.validator.settings.APP_MODE", "claude"):
        # Patch load_prompt
        with patch("backend.agents.validator.load_prompt") as mock_prompt:
            mock_prompt.return_value = "Test prompt"

            # Patch get_chat_model_for_agent
            with patch(
                "backend.agents.validator.get_chat_model_for_agent"
            ) as mock_get_model:
                # Setup mock chain
                mock_model = MagicMock()
                mock_model.model_name = "claude-sonnet-4-5"
                mock_runnable = MagicMock()
                mock_runnable.invoke.return_value = mock_response
                mock_model.with_structured_output.return_value = mock_runnable
                mock_get_model.return_value = mock_model

                # Patch _use_smart_validation
                with patch(
                    "backend.agents.validator._use_smart_validation", return_value=False
                ):
                    # Create test data
                    request = UserRequest(
                        construct_name="Test Construct",
                        construct_definition="Test definition for validation",
                        target_population="Adult participants",
                        response_scale="5-point Likert",
                        model_provider="claude",
                    )
                    items = [
                        DraftItem(
                            item_text="Test item",
                            construct_name="Test Construct",
                            rationale="This item tests the construct",
                        )
                    ]

                    # Should raise RuntimeError with informative message
                    with pytest.raises(
                        RuntimeError, match="Validator returned None.*no response from LLM"
                    ):
                        validate_items(request, items, attempt=1)


def test_validator_succeeds_with_valid_response():
    """Test that validator still works correctly with valid parsed response."""
    from backend.schemas import (
        DimensionScore,
        ItemValidation,
        ValidationResponse,
    )

    # Mock valid response
    valid_validation = ValidationResponse(
        validations=[
            ItemValidation(
                item_index=0,
                item_text="I feel anxious when facing uncertainty",
                dimension_scores=[
                    DimensionScore(
                        dimension="correspondence",
                        reasoning="Item aligns well with construct",
                        score=8,
                    ),
                    DimensionScore(
                        dimension="distinctiveness",
                        reasoning="Item is distinct",
                        score=8,
                    ),
                    DimensionScore(
                        dimension="clarity", reasoning="Clear wording", score=8
                    ),
                    DimensionScore(
                        dimension="specificity", reasoning="Specific enough", score=8
                    ),
                ],
                weighted_score=8.0,
                accept=True,
                attempt=1,
            )
        ]
    )

    mock_response = {"parsed": valid_validation, "raw": MagicMock()}

    # Patch settings.APP_MODE
    with patch("backend.agents.validator.settings.APP_MODE", "claude"):
        # Patch load_prompt
        with patch("backend.agents.validator.load_prompt") as mock_prompt:
            mock_prompt.return_value = "Test prompt"

            # Patch get_chat_model_for_agent
            with patch(
                "backend.agents.validator.get_chat_model_for_agent"
            ) as mock_get_model:
                # Setup mock chain
                mock_model = MagicMock()
                mock_model.model_name = "claude-sonnet-4-5"
                mock_runnable = MagicMock()
                mock_runnable.invoke.return_value = mock_response
                mock_model.with_structured_output.return_value = mock_runnable
                mock_get_model.return_value = mock_model

                # Patch _extract_token_usage
                with patch(
                    "backend.agents.validator._extract_token_usage"
                ) as mock_usage_fn:
                    from backend.agents.llm_utils import TokenUsage

                    mock_usage_fn.return_value = TokenUsage(
                        model_name="claude-sonnet-4-5",
                        input_tokens=100,
                        output_tokens=50,
                        total_tokens=150,
                    )

                    # Patch _use_smart_validation
                    with patch(
                        "backend.agents.validator._use_smart_validation",
                        return_value=False,
                    ):
                        # Create test data
                        request = UserRequest(
                            construct_name="Test",
                            construct_definition="Test definition for construct validation",
                            target_population="Adult participants",
                            response_scale="5-point Likert",
                            model_provider="claude",
                        )
                        items = [
                            DraftItem(
                                item_text="I feel anxious when facing uncertainty",
                                construct_name="Test",
                                rationale="This item measures the test construct",
                            )
                        ]

                        # Should succeed without raising
                        result, usage = validate_items(request, items, attempt=1)

                        # Verify result
                        assert result is not None
                        assert len(result.validations) == 1
                        assert result.validations[0].accept is True
                        assert usage.total_tokens == 150
