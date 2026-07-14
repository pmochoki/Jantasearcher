"""Handle Telegram inline button callbacks (approve, etc.)."""

from __future__ import annotations

from ats.runner import apply_to_job
from database.jobs import get_job
from notifications.telegram import (
    answer_callback_query,
    approval_reply_markup,
    edit_telegram_message,
    job_dashboard_url,
    send_telegram_message,
)


def handle_callback(
    callback_data: str,
    *,
    chat_id: str,
    callback_query_id: str,
    message_id: int | None,
) -> bool:
    if chat_id not in _allowed_chat_ids():
        return False

    if callback_data.startswith("approve:"):
        job_id = callback_data.split(":", 1)[1].strip()
        return _handle_approve_callback(
            job_id,
            chat_id=chat_id,
            callback_query_id=callback_query_id,
            message_id=message_id,
        )

    answer_callback_query(callback_query_id, text="Unknown action")
    return False


def _allowed_chat_ids() -> set[str]:
    from notifications.telegram import notify_chat_ids

    return set(notify_chat_ids())


def _handle_approve_callback(
    job_id: str,
    *,
    chat_id: str,
    callback_query_id: str,
    message_id: int | None,
) -> bool:
    job = get_job(job_id)
    if not job:
        answer_callback_query(callback_query_id, text="Job not found", alert=True)
        return False

    meta = job.metadata or {}
    if not meta.get("review_pending"):
        answer_callback_query(callback_query_id, text="Not awaiting approval", alert=True)
        return False

    answer_callback_query(callback_query_id, text="Submitting application…")

    if message_id is not None:
        edit_telegram_message(
            chat_id=chat_id,
            message_id=message_id,
            text=(
                "<b>ProjectEagle — Submitting…</b>\n"
                f"<b>{job.title}</b> @ {job.company}\n"
                "Please wait while the form is submitted."
            ),
            reply_markup={"inline_keyboard": []},
        )

    result = apply_to_job(job_id, force_submit=True)
    outcome = result.get("outcome", "unknown")
    message = result.get("message", "")
    dashboard = job_dashboard_url(job_id)

    final_text = (
        f"<b>ProjectEagle — Apply result</b>\n"
        f"<b>{job.title}</b> @ {job.company}\n"
        f"Outcome: <code>{outcome}</code>\n{message}\n\n"
        f"📋 <a href=\"{dashboard}\">View in dashboard</a>"
    )

    if message_id is not None:
        edit_telegram_message(chat_id=chat_id, message_id=message_id, text=final_text)
    else:
        send_telegram_message(final_text, chat_id=chat_id)

    return True
