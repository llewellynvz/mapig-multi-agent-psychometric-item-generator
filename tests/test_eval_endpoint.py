import os
import pytest

os.environ["APP_MODE"] = "mock"

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_run_evaluation_endpoint_returns_expected_structure():
    """POST /v1/run-evaluation returns structured JSON with success_criteria."""
    response = client.post("/v1/run-evaluation?model_provider=mock")

    assert response.status_code == 200
    data = response.json()

    # Verify top-level structure
    assert "current" in data
    assert "baseline" in data
    assert "improvement" in data
    assert "success_criteria" in data

    # Verify current metrics structure
    assert "item_quality_score" in data["current"]
    assert "agent_performance_score" in data["current"]
    assert "workflow_efficiency_score" in data["current"]
    assert "construct_validity_score" in data["current"]

    # Verify success criteria structure
    assert "meets_improvement_threshold" in data["success_criteria"]
    assert "all_dimensions_passing" in data["success_criteria"]
    assert "success" in data["success_criteria"]
    assert isinstance(data["success_criteria"]["success"], bool)
