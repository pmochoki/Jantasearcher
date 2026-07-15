from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from ai.errors import AiResponseError
from ai.tailor import tailor_for_job


def _mock_response(text: str) -> MagicMock:
    block = MagicMock()
    block.type = "text"
    block.text = text
    resp = MagicMock()
    resp.content = [block]
    resp.model = "claude-test"
    resp.usage = MagicMock(input_tokens=50, output_tokens=100)
    return resp


@patch("ai.tailor.get_claude_client")
def test_tailor_for_job_parses_json(mock_client):
    payload = {
        "tailored_resume": "# Resume",
        "cover_letter": "Dear hiring manager",
        "emphasized_skills": ["Python"],
        "notes": "",
    }
    mock_client.return_value.messages.create.return_value = _mock_response(json.dumps(payload))

    result = tailor_for_job({"skills": ["Python"]}, {"title": "Engineer", "description": "Python role"})

    assert result.cover_letter == "Dear hiring manager"
    assert result.tailored_resume == "# Resume"
    assert result.usage is not None
    assert result.usage.total_tokens == 150


@patch("ai.tailor.get_claude_client")
def test_tailor_for_job_invalid_json_raises(mock_client):
    mock_client.return_value.messages.create.return_value = _mock_response("not json")

    with pytest.raises(AiResponseError):
        tailor_for_job({}, {"title": "X", "description": "Y"})
