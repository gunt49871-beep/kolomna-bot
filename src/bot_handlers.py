import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ParseMode, ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

from src.config import config
from src.state_manager import get_state, save_state, reset_state, add_to_history
from src.ai_engine import get_ai_response
from src import appeals as appeal_module

logger = logging.getLogger(__name__)

APPEAL_BUTTON = "📨 Оставить обращение"
FAILED_ATTEMPTS_THRESHOLD = 2

MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [[KeyboardButton(APPEAL_BUTTON)]],
    resize_keyboard=True,
    input_field_placeholder="Задайте вопрос или оставьте обращение...",
)

WELCOME_TEXT = (
    "👋 Добро пожаловать в справочную службу администрации *городского округа Коломна*!\n\n"
    "Я помогу вам получить информацию по вопросам:\n"
    "🏗 Земельные и имущественные отношения\n"
    "🏪 Нестационарная торговля (НТО)\n"
    "📜 Расселение из аварийного жилья\n"
    "📋 Государственные услуги (РПГУ МО)\n"
    "📝 Обращения граждан\n\n"
    "Просто задайте вопрос — я постараюсь помочь!\n\n"
    "_Если не смогу ответить — нажмите кнопку_ 📨 *Оставить обращение* _внизу экрана._"
)

HELP_TEXT = (
    "ℹ️ *Справочная служба Коломны*\n\n"
    "Я отвечаю на вопросы по:\n"
    "• Оформлению земельных участков\n"
    "• Нестационарной торговле\n"
    "• Расселению из аварийного жилья\n"
    "• Государственным услугам (РПГУ МО)\n"
    "• Порядку подачи обращений граждан\n\n"
    "📞 Администрация Коломны: +7 (496) 612-21-11\n"
    "📍 Пл. Советская, д. 1\n"
    "🌐 kolomnagrad.ru\n\n"
    "Нажмите 📨 *Оставить обращение*, чтобы направить официальное обращение."
)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await reset_state(user_id)
    await update.message.reply_text(
        WELCOME_TEXT,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=MAIN_KEYBOARD,
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        HELP_TEXT,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=MAIN_KEYBOARD,
    )


async def cmd_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await reset_state(user_id)
    await update.message.reply_text(
        "🔄 Диалог сброшен. Задайте новый вопрос!",
        reply_markup=MAIN_KEYBOARD,
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text.strip()

    if text == APPEAL_BUTTON:
        await _start_appeal(update, user.id)
        return

    state = await get_state(user.id)

    # Если идёт заполнение формы обращения
    if state.get("appeal_step"):
        await _process_appeal_step(update, state, text)
        return

    # Обычный AI-диалог
    await update.message.chat.send_action(ChatAction.TYPING)
    reply, suggest_appeal = await get_ai_response(state["history"], text)

    add_to_history(state, "user", text)
    add_to_history(state, "assistant", reply)

    if suggest_appeal:
        state["failed_attempts"] = state.get("failed_attempts", 0) + 1
    else:
        state["failed_attempts"] = 0

    await save_state(user.id, state)
    await update.message.reply_text(reply, parse_mode=ParseMode.MARKDOWN, reply_markup=MAIN_KEYBOARD)

    if state["failed_attempts"] >= FAILED_ATTEMPTS_THRESHOLD:
        state["failed_attempts"] = 0
        await save_state(user.id, state)
        await update.message.reply_text(
            "🤔 Похоже, я не смог дать исчерпывающий ответ на ваш вопрос.\n\n"
            "Хотите оставить *официальное обращение* в администрацию Коломны? "
            "Сотрудники рассмотрят его в течение 30 дней (ФЗ №59).",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📨 Да, оставить обращение", callback_data="start_appeal")],
                [InlineKeyboardButton("💬 Продолжить диалог", callback_data="continue_chat")],
            ]),
        )


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    data = query.data

    if data == "start_appeal":
        await query.message.delete()
        await _start_appeal(update, user.id, via_query=True, message=query.message)
        return

    if data == "continue_chat":
        await query.message.delete()
        return

    if data.startswith("topic_"):
        topic_code = data[len("topic_"):]
        state = await get_state(user.id)
        state["appeal_data"]["topic"] = topic_code
        state["appeal_step"] = "description"
        await save_state(user.id, state)
        await query.edit_message_text(
            appeal_module.STEP_QUESTIONS["description"],
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    if data == "appeal_confirm":
        state = await get_state(user.id)
        appeal_data = state.get("appeal_data", {})
        success = await appeal_module.send_appeal_to_admin(appeal_data, user)
        state["appeal_step"] = None
        state["appeal_data"] = {"name": None, "phone": None, "topic": None, "description": None}
        await save_state(user.id, state)

        if success:
            await query.edit_message_text(
                "✅ *Обращение успешно отправлено!*\n\n"
                "Ваше обращение передано сотрудникам администрации Коломны.\n"
                "Срок рассмотрения — до 30 рабочих дней (ФЗ №59).\n\n"
                "Если возникнут дополнительные вопросы, задайте их ниже.",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=None,
            )
        else:
            await query.edit_message_text(
                "⚠️ Произошла техническая ошибка при отправке обращения.\n"
                "Пожалуйста, обратитесь напрямую:\n"
                "📞 +7 (496) 612-21-11\n"
                "📍 Пл. Советская, д. 1\n"
                "✉️ kolomna@mosreg.ru",
                parse_mode=ParseMode.MARKDOWN,
            )
        return

    if data == "appeal_cancel":
        state = await get_state(user.id)
        state["appeal_step"] = None
        state["appeal_data"] = {"name": None, "phone": None, "topic": None, "description": None}
        await save_state(user.id, state)
        await query.edit_message_text(
            "❌ Обращение отменено. Можете задать новый вопрос или снова нажать 📨 *Оставить обращение*.",
            parse_mode=ParseMode.MARKDOWN,
        )


async def _start_appeal(update: Update, user_id: int, via_query: bool = False, message=None):
    state = await get_state(user_id)
    state["appeal_step"] = "name"
    state["appeal_data"] = {"name": None, "phone": None, "topic": None, "description": None}
    await save_state(user_id, state)

    text = (
        "📨 *Форма обращения в администрацию Коломны*\n\n"
        "Заполним вместе — это займёт 1 минуту.\n\n"
        + appeal_module.STEP_QUESTIONS["name"]
    )

    if via_query and message:
        await message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=MAIN_KEYBOARD)
    else:
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=MAIN_KEYBOARD)


async def _process_appeal_step(update: Update, state: dict, text: str):
    step = state["appeal_step"]
    user_id = update.effective_user.id

    if step == "name":
        state["appeal_data"]["name"] = text
        state["appeal_step"] = "phone"
        await save_state(user_id, state)
        await update.message.reply_text(
            appeal_module.STEP_QUESTIONS["phone"],
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=MAIN_KEYBOARD,
        )

    elif step == "phone":
        state["appeal_data"]["phone"] = text
        state["appeal_step"] = "topic"
        await save_state(user_id, state)
        await update.message.reply_text(
            "📂 Выберите *тему обращения*:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=appeal_module.get_topic_keyboard(),
        )

    elif step == "description":
        state["appeal_data"]["description"] = text
        state["appeal_step"] = "confirm"
        await save_state(user_id, state)
        preview = appeal_module.format_appeal_preview(state["appeal_data"])
        await update.message.reply_text(
            preview,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=appeal_module.get_confirm_keyboard(),
        )

    elif step == "confirm":
        # На этапе подтверждения ждём нажатия кнопок, текст игнорируем
        await update.message.reply_text(
            "Пожалуйста, воспользуйтесь кнопками ✅ *Отправить* или ❌ *Отмена* выше.",
            parse_mode=ParseMode.MARKDOWN,
        )


def setup_application(app: Application):
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("reset", cmd_reset))
    app.add_handler(CommandHandler("новый", cmd_reset))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
