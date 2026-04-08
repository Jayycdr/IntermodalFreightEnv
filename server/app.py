"""
Server entry point for multi-mode deployment.

This file serves as the main application entry point for deployment systems.
It imports and exposes the FastAPI application from the main module.
"""

from app.main import app

__all__ = ["app"]
