from __future__ import annotations

import logging
import os
import tempfile
from typing import List

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from assistant.formatting import format_capture_response, format_items
from assistant.models import Clarification
from assistant.service import AssistantService

LOGGER = logging.getLogger(__name__)


def build_application(token: str, service: AssistantService):
    application = ApplicationBuilder().token(token).build()
    application.bot_data["service"] = service

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("plan_today", plan_today))
    application.add_handler(CommandHandler("plan_week", plan_week))
    application.add_handler(CommandHandler("tasks", list_tasks))
    application.add_handler(CommandHandler("search", search))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.add_handler(
        MessageHandler(filters.VOICE & ~filters.COMMAND, handle_voice)
    )
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text)
    )
    return application


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = (
        "Hello! Send a message or voice note to capture tasks, notes, ideas, "
        "events, and decisions.\n"
        "Commands: /plan_today, /plan_week, /tasks [context], /search <query>."
    )
    await update.message.reply_text(message)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await start(update, context)


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    service: AssistantService = context.application.bot_data["service"]
    user_id = str(update.effective_user.id)
    text = (update.message.text or "").strip()
    if not text:
        return

    if await _maybe_answer_clarification(update, context, service, user_id, text):
        return

    result = service.capture(user_id=user_id, message=text, source="text")
    response = format_capture_response(result.summary, result.items)
    await update.message.reply_text(response)
    await _send_clarifications(update, result.clarifications)


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    service: AssistantService = context.application.bot_data["service"]
    user_id = str(update.effective_user.id)
    voice = update.message.voice
    if not voice:
        return

    file = await context.bot.get_file(voice.file_id)
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, "voice.ogg")
        await file.download_to_drive(file_path)
        try:
            transcript = service.transcribe_voice(file_path)
        except Exception as exc:  # noqa: BLE001
            LOGGER.exception("Transcription failed: %s", exc)
            await update.message.reply_text("Failed to transcribe voice message.")
            return

    if not transcript:
        await update.message.reply_text("Could not understand the voice message.")
        return

    result = service.capture(user_id=user_id, message=transcript, source="voice")
    response = format_capture_response(result.summary, result.items)
    await update.message.reply_text(
        f"Transcript: {transcript}\n\n{response}"
    )
    await _send_clarifications(update, result.clarifications)


async def plan_today(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    service: AssistantService = context.application.bot_data["service"]
    user_id = str(update.effective_user.id)
    rows = service.plan_today(user_id)
    await update.message.reply_text(format_items("Today's plan:", rows))


async def plan_week(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    service: AssistantService = context.application.bot_data["service"]
    user_id = str(update.effective_user.id)
    rows = service.plan_week(user_id)
    await update.message.reply_text(format_items("This week's plan:", rows))


async def list_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    service: AssistantService = context.application.bot_data["service"]
    user_id = str(update.effective_user.id)
    context_arg = None
    if context.args:
        context_arg = context.args[0].strip().lower()
    rows = service.list_tasks(user_id, context=context_arg)
    await update.message.reply_text(format_items("Open tasks:", rows))


async def search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    service: AssistantService = context.application.bot_data["service"]
    user_id = str(update.effective_user.id)
    query = " ".join(context.args).strip()
    if not query:
        await update.message.reply_text("Usage: /search <query>")
        return
    rows = service.search(user_id, query)
    await update.message.reply_text(format_items("Search results:", rows))


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    service: AssistantService = context.application.bot_data["service"]
    query = update.callback_query
    if not query:
        return
    await query.answer()
    data = query.data or ""
    if not data.startswith("clarify:"):
        return
    parts = data.split(":", 2)
    if len(parts) != 3:
        return
    _, clar_id, value = parts
    clarification = _find_clarification(service, query.from_user.id, clar_id)
    if not clarification:
        await query.edit_message_text("Clarification expired.")
        return
    ok, message = service.answer_clarification(clarification, value)
    await query.edit_message_text(message)


def _find_clarification(
    service: AssistantService, user_id: int, clar_id: str
) -> Clarification | None:
    pending = service.pending_clarifications(str(user_id))
    for clar in pending:
        if clar.id == clar_id:
            return clar
    return None


async def _maybe_answer_clarification(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    service: AssistantService,
    user_id: str,
    text: str,
) -> bool:
    pending = service.pending_clarifications(user_id)
    if len(pending) == 1:
        ok, message = service.answer_clarification(pending[0], text)
        await update.message.reply_text(message)
        return True
    if len(pending) > 1:
        await update.message.reply_text(
            "Please answer clarification questions using the buttons."
        )
        return True
    return False


async def _send_clarifications(
    update: Update, clarifications: List[Clarification]
) -> None:
    if not clarifications:
        return
    for clar in clarifications:
        keyboard = _keyboard_for_clarification(clar)
        await update.message.reply_text(
            clar.question,
            reply_markup=keyboard,
        )


def _keyboard_for_clarification(
    clarification: Clarification,
) -> InlineKeyboardMarkup | None:
    if not clarification.options:
        return None
    buttons = [
        InlineKeyboardButton(
            text=option,
            callback_data=f"clarify:{clarification.id}:{_safe_callback_value(option)}",
        )
        for option in clarification.options[:4]
    ]
    return InlineKeyboardMarkup.from_row(buttons)


def _safe_callback_value(option: str) -> str:
    return option.replace(":", "-")[:32]
