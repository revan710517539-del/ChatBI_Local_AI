"""Vercel FastAPI entrypoint.

Vercel's Python runtime auto-detects `app.py` and expects an `app` variable.
This module re-exports the application defined in `chatbi.main`.
"""

from chatbi.main import app

