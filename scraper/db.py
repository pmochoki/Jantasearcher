"""Backward-compatible re-exports. Prefer `database.db` for new code."""

from database.db import init_db, save_jobs

__all__ = ["init_db", "save_jobs"]
