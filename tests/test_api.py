"""Test suite for API validation response.

This module tests the FastAPI endpoint integration with validation,
ensuring validation results are included in API responses.
"""

import os
import pytest

os.environ["APP_MODE"] = "mock"


def test_validation_in_response():
    """Verify POST /generate returns FinalOutput with validation_result per final_item.

    Tests VAL-08: Validation scores and reasoning visible in results UI.

    Expected behavior:
    - POST /generate with valid UserRequest returns 200 OK
    - Response body is FinalOutput schema
    - FinalOutput.validation_results exists and is non-empty
    - Each final_item has corresponding ValidationResult at same index
    - ValidationResult includes all 4 dimension_scores with reasoning
    - ValidationResult includes weighted_score and accept status
    - API response is valid JSON with all validation metadata
    - Frontend can render dimension scores and reasoning from response
    """
    pytest.skip("Awaiting API validation integration in plan 01-05")
