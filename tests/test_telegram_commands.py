"""Unit tests for Telegram bot command routing."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from notifications.telegram_bot import _normalize_command
from notifications.telegram_commands import (
    AUTOMATIC_ALERTS,
    COMMAND_CATALOG,
    _resolve_handler,
    dispatch_command,
)


class TestNormalizeCommand(unittest.TestCase):
    def test_strips_bot_suffix(self) -> None:
        self.assertEqual(_normalize_command("/list@JantaSecretarybot"), "/list")
        self.assertEqual(
            _normalize_command("/approve@JantaSecretarybot abc123"),
            "/approve abc123",
        )

    def test_preserves_args(self) -> None:
        self.assertEqual(
            _normalize_command("/answer job-id yes I have 5 years"),
            "/answer job-id yes I have 5 years",
        )


class TestCommandCatalog(unittest.TestCase):
    def test_catalog_has_all_handlers(self) -> None:
        from notifications.telegram_commands import _HANDLERS

        keys = {row[3] for row in COMMAND_CATALOG}
        self.assertTrue(keys.issubset(set(_HANDLERS.keys())))

    def test_automatic_alerts_nonempty(self) -> None:
        self.assertGreaterEqual(len(AUTOMATIC_ALERTS), 5)


class TestResolveHandler(unittest.TestCase):
    def test_essential_commands(self) -> None:
        for cmd in ("/list", "/help", "/start", "/ping", "/status"):
            self.assertIsNotNone(_resolve_handler(cmd), cmd)

    def test_info_commands(self) -> None:
        for cmd in ("/summary", "/stats", "/jobs", "/jobs 5", "/job abc"):
            self.assertIsNotNone(_resolve_handler(cmd), cmd)

    def test_apply_commands(self) -> None:
        self.assertIsNotNone(_resolve_handler("/approve uuid"))
        self.assertIsNotNone(_resolve_handler("/answer uuid text"))

    def test_scraper_commands(self) -> None:
        for cmd in (
            "/scan eu",
            "/scan scholarships",
            "/scan linkedin",
            "/scan profession",
            "/canary",
        ):
            self.assertIsNotNone(_resolve_handler(cmd), cmd)

    def test_unknown_returns_none(self) -> None:
        self.assertIsNone(_resolve_handler("/notreal"))
        self.assertIsNone(_resolve_handler("/scan mars"))


class TestDispatchCommand(unittest.TestCase):
    @patch("notifications.telegram_commands.send_telegram_message")
    def test_ping(self, mock_send: MagicMock) -> None:
        self.assertTrue(dispatch_command("/ping", "12345"))
        mock_send.assert_called_once()
        self.assertIn("OK", mock_send.call_args[0][0])

    @patch("notifications.telegram_commands.send_command_list")
    def test_list(self, mock_list: MagicMock) -> None:
        self.assertTrue(dispatch_command("/list", "12345"))
        mock_list.assert_called_once_with(chat_id="12345")

    @patch("notifications.telegram_commands.send_daily_summary")
    @patch("database.jobs.get_stats")
    def test_summary(self, mock_stats: MagicMock, mock_summary: MagicMock) -> None:
        mock_stats.return_value = {"total": 1}
        self.assertTrue(dispatch_command("/summary", "12345"))
        mock_summary.assert_called_once()

    @patch("notifications.telegram_commands.send_telegram_message")
    def test_unknown_not_dispatched(self, mock_send: MagicMock) -> None:
        self.assertFalse(dispatch_command("/foobar", "12345"))
        mock_send.assert_not_called()


if __name__ == "__main__":
    unittest.main()
