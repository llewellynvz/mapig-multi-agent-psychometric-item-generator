"""Tests for CORS configuration supporting Vercel deployment.

Validates that CORS middleware allows Vercel production/preview domains.
"""
import pytest
import re
from fastapi.testclient import TestClient


def test_cors_allows_localhost():
    """CORS allows localhost for local development."""
    from app.main import app
    client = TestClient(app)

    response = client.options(
        "/healthz",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        }
    )

    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
    assert "http://localhost:3000" in response.headers.get("access-control-allow-origin", "")


def test_cors_allows_vercel_preview_domains():
    """CORS allows Vercel preview deployment domains."""
    from app.main import app
    client = TestClient(app)

    # Test pattern: https://project-abc123.vercel.app
    vercel_preview_origin = "https://mapig-frontend-abc123.vercel.app"

    response = client.options(
        "/healthz",
        headers={
            "Origin": vercel_preview_origin,
            "Access-Control-Request-Method": "POST",
        }
    )

    # Should allow based on regex pattern
    assert response.status_code == 200
    # Verify CORS headers present
    assert "access-control-allow-origin" in response.headers


def test_cors_allows_vercel_production_domains():
    """CORS allows Vercel production domains."""
    from app.main import app
    client = TestClient(app)

    # Test pattern: https://project.vercel.app
    vercel_prod_origin = "https://mapig-frontend.vercel.app"

    response = client.options(
        "/healthz",
        headers={
            "Origin": vercel_prod_origin,
            "Access-Control-Request-Method": "POST",
        }
    )

    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers


def test_cors_regex_pattern_matches_vercel():
    """CORS configuration includes regex pattern for *.vercel.app domains."""
    from app.main import app

    # Find CORSMiddleware in app.middleware
    cors_middleware = None
    for middleware in app.user_middleware:
        if "CORSMiddleware" in str(middleware):
            cors_middleware = middleware
            break

    # This test validates the configuration exists
    # Full validation requires inspecting middleware options
    pytest.skip("Requires middleware introspection - implement in Wave 1")


def test_cors_credentials_allowed():
    """CORS allows credentials for authenticated requests."""
    from app.main import app
    client = TestClient(app)

    response = client.options(
        "/healthz",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        }
    )

    assert "access-control-allow-credentials" in response.headers
    assert response.headers["access-control-allow-credentials"] == "true"
