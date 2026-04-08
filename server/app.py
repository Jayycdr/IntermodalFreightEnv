"""
Server entry point for multi-mode deployment.

This file serves as the main application entry point for deployment systems.
It imports and exposes the FastAPI application from the main module.
"""

from app.main import app


def main():
    """Main entry point function."""
    return app


__all__ = ["app", "main"]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
