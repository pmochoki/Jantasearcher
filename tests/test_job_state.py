from __future__ import annotations

import pytest

from database.job_state import append_status_history, can_transition


def test_allowed_status_transitions():
    assert can_transition("new", "queued")
    assert can_transition("queued", "applied")
    assert can_transition("applied", "failed")
    assert not can_transition("applied", "new")
    assert not can_transition("skipped", "applied")


def test_status_history_appends():
    meta = append_status_history({}, from_status="new", to_status="queued", reason="manual")
    assert meta["status_history"][-1]["to"] == "queued"
    assert meta["status_history"][-1]["reason"] == "manual"


def test_invalid_transition_raises_in_update_job_status():
    from unittest.mock import MagicMock, patch

    from database.jobs import update_job_status

    job = MagicMock()
    job.status = "skipped"
    job.metadata = {}

    with patch("database.jobs.get_job", return_value=job):
        with pytest.raises(ValueError, match="Invalid status transition"):
            update_job_status("job-id", "applied")
