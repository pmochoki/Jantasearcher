from __future__ import annotations

from ai.usage import AiUsage, extract_usage, merge_ai_usage


class _Usage:
    input_tokens = 120
    output_tokens = 80


class _Response:
    model = "claude-test"
    usage = _Usage()


def test_extract_usage():
    usage = extract_usage(_Response(), operation="test_op")
    assert usage.model == "claude-test"
    assert usage.input_tokens == 120
    assert usage.output_tokens == 80
    assert usage.operation == "test_op"
    assert usage.total_tokens == 200


def test_merge_ai_usage_accumulates():
    usage = AiUsage(model="m", input_tokens=10, output_tokens=5, operation="tailor")
    meta = merge_ai_usage({}, usage)
    assert meta["ai_tokens_total"] == 15
    assert len(meta["ai_usage_log"]) == 1
    meta2 = merge_ai_usage(meta, usage)
    assert meta2["ai_tokens_total"] == 30
    assert len(meta2["ai_usage_log"]) == 2
