"""Vercel serverless entry point for MAPIG FastAPI application.

Vercel automatically detects and wraps ASGI apps exported from this location.
Native ASGI support - no adapter needed (Mangum is AWS Lambda-specific).

Reference: https://vercel.com/docs/frameworks/backend/fastapi
"""
from backend.main import app

# Vercel automatically wraps this ASGI app for serverless execution
# The 'app' export is detected and configured as a Vercel Function
