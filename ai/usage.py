"""Track Claude API token usage per operation."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class AiUsage:
    model: str
    input_tokens: int
    output_tokens: int
    operation: str

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def extract_usage(response: Any, *, operation: str) -> AiUsage:
    """Extract token counts from an Anthropic Messages API response."""
    usage = getattr(response, "usage", None)
    model = getattr(response, "model", "") or ""
    return AiUsage(
        model=model,
        input_tokens=int(getattr(usage, "input_tokens", 0) or 0),
        output_tokens=int(getattr(usage, "output_tokens", 0) or 0),
        operation=operation,
    )


def merge_ai_usage(metadata: dict[str, Any], usage: AiUsage) -> dict[str, Any]:
    """Append usage to job metadata and update running totals."""
    meta = dict(metadata)
    log = list(meta.get("ai_usage_log") or [])
    entry = {
        **usage.to_dict(),
        "at": datetime.now(timezone.utc).isoformat(),
    }
    log.append(entry)
    meta["ai_usage_log"] = log[-50:]
    meta["ai_tokens_total"] = int(meta.get("ai_tokens_total") or 0) + usage.total_tokens
    return meta
