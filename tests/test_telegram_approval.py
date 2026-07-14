"""Tests for Telegram approval buttons and callbacks."""

from __future__ import annotations

import unittest

from notifications.telegram import approval_reply_markup, job_dashboard_url


class TestApprovalButtons(unittest.TestCase):
    def test_reply_markup_has_approve_and_links(self) -> None:
        job_id = "152fb4e6-0347-4825-a274-cdedd758b63f"
        external = "https://boards.greenhouse.io/example/jobs/123"
        markup = approval_reply_markup(job_id=job_id, external_url=external)
        keyboard = markup["inline_keyboard"]
        self.assertEqual(keyboard[0][0]["callback_data"], f"approve:{job_id}")
        self.assertEqual(keyboard[0][0]["text"], "✅ Approve & submit")
        urls = {btn.get("url") for row in keyboard for btn in row if "url" in btn}
        self.assertIn(external, urls)
        self.assertIn(job_dashboard_url(job_id), urls)

    def test_callback_data_under_64_bytes(self) -> None:
        job_id = "152fb4e6-0347-4825-a274-cdedd758b63f"
        data = approval_reply_markup(job_id=job_id, external_url="https://example.com")[
            "inline_keyboard"
        ][0][0]["callback_data"]
        self.assertLessEqual(len(data.encode()), 64)


if __name__ == "__main__":
    unittest.main()
