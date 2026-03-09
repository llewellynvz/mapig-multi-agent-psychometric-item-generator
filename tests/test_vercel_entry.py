"""Tests for Vercel serverless entry point.

Validates DEP-01: FastAPI app is correctly exposed via api/index.py for Vercel.
"""
import pytest
from fastapi import FastAPI


def test_api_index_exports_app():
    """Vercel entry point exports 'app' instance."""
    from api.index import app

    assert app is not None, "api/index.py should export 'app'"
    assert isinstance(app, FastAPI), "Exported 'app' should be FastAPI instance"


def test_api_routes_accessible():
    """Core API routes are available through Vercel entry point."""
    from api.index import app

    routes = [route.path for route in app.routes]

    assert "/healthz" in routes, "Health check endpoint should be available"
    assert "/v1/generate-items-stream" in routes, "SSE stream endpoint should be available"


def test_app_title_configured():
    """FastAPI app has correct metadata for documentation."""
    from api.index import app

    assert app.title == "MAPIG: Multi-Agent Psychometric Item Generator"
    assert app.version is not None
