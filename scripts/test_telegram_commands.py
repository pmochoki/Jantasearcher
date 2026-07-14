#!/usr/bin/env python3
"""Live Telegram command smoke test — sends safe read-only commands."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")

from notifications.telegram import notify_chat_ids, send_telegram_message, telegram_status
from notifications.telegram_bot import _handle_message, start_telegram_bot_background, telegram_bot_status
from notifications.telegram_commands import register_bot_commands_with_telegram


def main() -> int:
    chat_id = (notify_chat_ids() or [""])[0]
    if not chat_id:
        print("ERROR: TELEGRAM_CHAT_ID not set")
        return 1

    status = telegram_status()
    print("Telegram status:", status)

    registered = register_bot_commands_with_telegram()
    print("setMyCommands:", "ok" if registered else "failed")

    safe_commands = ["/ping", "/status", "/summary", "/jobs 3", "/list"]
    send_telegram_message(
        "<b>ProjectEagle — command smoke test</b>\nRunning: "
        + ", ".join(f"<code>{c}</code>" for c in safe_commands),
        chat_id=chat_id,
    )

    for cmd in safe_commands:
        print(f"Dispatching {cmd}...")
        _handle_message(cmd, chat_id)
        time.sleep(0.5)

    start_telegram_bot_background()
    bot = telegram_bot_status()
    print("Bot thread:", bot.get("bot_thread_alive"))

    send_telegram_message(
        "<b>Smoke test complete.</b> Scraper commands (/scan eu, etc.) were not run "
        "to avoid long Playwright jobs — trigger those manually if needed.",
        chat_id=chat_id,
    )
    print("Done — check Telegram for replies.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
