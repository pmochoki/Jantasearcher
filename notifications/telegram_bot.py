from __future__ import annotations

import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

LAST_SUMMARY_FILE = PROJECT_ROOT / "data" / ".last_daily_summary"
POLL_OFFSET_FILE = PROJECT_ROOT / "data" / ".telegram_offset"

_bot_thread: threading.Thread | None = None
_stop_event = threading.Event()


def _token() -> str:
    return os.getenv("TELEGRAM_BOT_TOKEN", "").strip()


def _chat_id() -> str:
    return os.getenv("TELEGRAM_CHAT_ID", "").strip()


def _allowed_chat_ids() -> set[str]:
    from notifications.telegram import notify_chat_ids

    return set(notify_chat_ids())


def _normalize_command(text: str) -> str:
    """Strip @BotName suffix from channel commands like /list@MyBot."""
    text = text.strip()
    if not text.startswith("/"):
        return text
    first, *rest = text.split(maxsplit=1)
    command = first.split("@", 1)[0]
    return f"{command} {rest[0]}".strip() if rest else command


def _extract_incoming(update: dict) -> tuple[str, str] | None:
    """Return (text, chat_id) from a private message or channel post."""
    for key in ("message", "channel_post", "edited_message", "edited_channel_post"):
        payload = update.get(key) or {}
        text = payload.get("text") or ""
        chat = payload.get("chat") or {}
        chat_id = chat.get("id")
        if text and chat_id is not None:
            return _normalize_command(text), str(chat_id)
    return None


def _extract_callback(update: dict) -> tuple[str, str, str, int | None] | None:
    """Return (callback_data, chat_id, callback_query_id, message_id)."""
    cb = update.get("callback_query") or {}
    data = cb.get("data") or ""
    cb_id = cb.get("id")
    msg = cb.get("message") or {}
    chat = msg.get("chat") or {}
    chat_id = chat.get("id")
    message_id = msg.get("message_id")
    if not data or cb_id is None or chat_id is None:
        return None
    return data, str(chat_id), str(cb_id), message_id


def _get_updates(offset: int | None) -> list[dict]:
    token = _token()
    if not token:
        return []
    params: dict = {"timeout": 25}
    if offset is not None:
        params["offset"] = offset
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    try:
        resp = httpx.get(url, params=params, timeout=30.0)
        data = resp.json()
        if data.get("ok"):
            return data.get("result", [])
    except httpx.HTTPError:
        pass
    return []


def _load_offset() -> int | None:
    if POLL_OFFSET_FILE.exists():
        try:
            return int(POLL_OFFSET_FILE.read_text().strip())
        except ValueError:
            pass
    return None


def _save_offset(offset: int) -> None:
    POLL_OFFSET_FILE.parent.mkdir(parents=True, exist_ok=True)
    POLL_OFFSET_FILE.write_text(str(offset), encoding="utf-8")


def _handle_callback(
    callback_data: str,
    chat_id: str,
    callback_query_id: str,
    message_id: int | None,
) -> None:
    from notifications.telegram_callbacks import handle_callback

    if chat_id not in _allowed_chat_ids():
        return
    handle_callback(
        callback_data,
        chat_id=chat_id,
        callback_query_id=callback_query_id,
        message_id=message_id,
    )


def _handle_message(text: str, chat_id: str) -> None:
    from notifications.telegram import send_telegram_message
    from notifications.telegram_commands import dispatch_command

    if chat_id not in _allowed_chat_ids():
        return

    text = text.strip()

    if dispatch_command(text, chat_id):
        return

    if text.startswith("/"):
        send_telegram_message(
            "Unknown command. Send <code>/list</code> to see available commands.",
            chat_id=chat_id,
        )


def _prepare_polling() -> bool:
    from notifications.telegram import ensure_polling_mode, send_startup_message, telegram_status
    from notifications.telegram_commands import register_bot_commands_with_telegram

    status = telegram_status()
    if not status.get("configured"):
        return False
    if status.get("webhook_blocks_polling"):
        ensure_polling_mode()
    register_bot_commands_with_telegram()
    send_startup_message()
    return True


def _poll_loop() -> None:
    offset = _load_offset()
    while not _stop_event.is_set():
        updates = _get_updates(offset)
        for update in updates:
            offset = update["update_id"] + 1
            _save_offset(offset)
            incoming = _extract_incoming(update)
            if incoming:
                text, chat_id = incoming
                _handle_message(text, chat_id)
                continue

            callback = _extract_callback(update)
            if callback:
                data, chat_id, cb_id, msg_id = callback
                _handle_callback(data, chat_id, cb_id, msg_id)

        _maybe_send_daily_summary()
        time.sleep(1)


def _summary_now() -> datetime:
    tz_name = os.getenv("DAILY_SUMMARY_TIMEZONE", "").strip()
    if tz_name:
        from zoneinfo import ZoneInfo

        return datetime.now(ZoneInfo(tz_name))
    return datetime.now(timezone.utc)


def _summary_target_hour() -> int:
    tz_name = os.getenv("DAILY_SUMMARY_TIMEZONE", "").strip()
    if tz_name:
        return int(os.getenv("DAILY_SUMMARY_HOUR_LOCAL", "22"))
    return int(os.getenv("DAILY_SUMMARY_HOUR_UTC", "7"))


def _maybe_send_daily_summary() -> None:
    from database.jobs import get_stats
    from notifications.telegram import send_daily_summary

    now = _summary_now()
    if now.hour != _summary_target_hour():
        return

    today = now.date().isoformat()
    if LAST_SUMMARY_FILE.exists() and LAST_SUMMARY_FILE.read_text().strip() == today:
        return

    send_daily_summary(get_stats())
    LAST_SUMMARY_FILE.parent.mkdir(parents=True, exist_ok=True)
    LAST_SUMMARY_FILE.write_text(today, encoding="utf-8")


def start_telegram_bot_background() -> None:
    global _bot_thread
    if not _token() or not _allowed_chat_ids():
        return
    if _bot_thread and _bot_thread.is_alive():
        return

    if not _prepare_polling():
        return

    _stop_event.clear()
    _bot_thread = threading.Thread(target=_poll_loop, name="telegram-bot", daemon=True)
    _bot_thread.start()


def stop_telegram_bot() -> None:
    _stop_event.set()


def telegram_bot_status() -> dict:
    from notifications.telegram import telegram_status

    status = telegram_status()
    status["bot_thread_alive"] = bool(_bot_thread and _bot_thread.is_alive())
    return status
