"""Typed errors for AI module."""

from __future__ import annotations


class AiResponseError(Exception):
    """Claude returned content that could not be parsed or validated."""

    def __init__(self, message: str, *, raw: str | None = None) -> None:
        super().__init__(message)
        self.raw = raw
