"""Compatibility entrypoint for existing `uvicorn backend.main:app` commands."""

from backend.app.main import app, create_app

__all__ = ["app", "create_app"]
