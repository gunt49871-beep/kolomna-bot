import logging
from datetime import datetime, timezone, timedelta
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from src.config import config

logger = logging.getLogger(__name__)

MOSCOW_TZ = timezone(timedelta(hours=3))

TOPICS = [
    ("🏗 Земельные отношения",              "land"),
    ("🏠 Имущественные отношения",           "property"),
    ("📜 Расселение из аварийного жилья",    "resettlement"),
    ("🏪 Нестационарная торговля (НТО)",     "trade"),
    ("📋 Государственные услуги (РПГУ/МФЦ)", "services"),
    ("🔧 ЖКХ и коммунальные услуги",         "communal"),
    ("🚗 Дороги, транспорт, парковки",       "roads"),
    ("🏢 Строительство и градостроительство","construction"),
    ("🌿 Благоустройство и экология",        "beautification"),
    ("🎓 Образование, культура, спорт",      "social"),
    ("💼 Бизнес и предпринимательство",      "business"),
    ("🛡 Безопасность и правопорядок",       "safety"),
    ("📝 Другое",                            "other"),
]

# Ответственные заместители главы по темам (Распоряжение главы г.о. Коломна от 20.05.2024 №32)
# Используется только в admin-сообщении — пользователям не показывается
TOPIC_TO_DEPUTY = {
    "land":         "Зам. главы ПОТИХА Кристина Игоревна (земельные отношения, земельный контроль)",
    "property":     "Зам. главы ПОТИХА Кристина Игоревна (имущественные и земельные отношения)",
    "resettlement": "Зам. главы ПОТИХА Кристина Игоревна (расселение из аварийного жилья, жилфонд)",
    "trade":        "Зам. главы ПОТИХА К.И. (размещение НТО, аукцион) + ПАНЧИШНЫЙ Р.С. (торговая деятельность, схема НТО)",
    "services":     "Зам. главы ДМИТРИЕВА Ирина Викторовна (госуслуги, МФЦ, РПГУ МО)",
    "communal":     "Зам. главы ХОДАСЕВИЧ Дмитрий Игоревич (ЖКХ, тепло, вода, газ, УК/ТСЖ)",
    "roads":        "Зам. главы КОТОВ Денис Сергеевич (дороги, транспорт, парковки, ТКО/мусор)",
    "construction": "Зам. главы ЦАПЛИНСКИЙ Сергей Михайлович (строительство, градостроительство, ПЗЗ)",
    "beautification":"1-й зам. главы ЛУБЯНОЙ Денис Борисович (правила благоустройства, контроль) / КОТОВ Д.С. (дворы, ТКО)",
    "social":       "Зам. главы ЛУНЬКОВА Лариса Николаевна (образование, культура, спорт, соцзащита)",
    "business":     "Зам. главы ПАНЧИШНЫЙ Роман Сергеевич (экономика, малый бизнес, ярмарки)",
    "safety":       "Зам. главы КОНОВАЛОВ Максим Викторович (безопасность, ГО и ЧС, правопорядок)",
    "other":        "1-й зам. главы ЛУБЯНОЙ Денис Борисович (общая координация)",
}

APPEAL_STEPS = ["name", "phone", "topic", "description", "confirm"]

STEP_QUESTIONS = {
    "name": "👤 Введите ваши **Фамилию и Имя** (например: Иванов Иван):",
    "phone": "📱 Введите ваш **номер телефона** для обратной связи:",
    "description": "📋 Опишите суть вашего обращения подробно:",
    "confirm": None,
}


def get_topic_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(label, callback_data=f"topic_{code}")]
        for label, code in TOPICS
    ]
    return InlineKeyboardMarkup(buttons)


def get_topic_label(code: str) -> str:
    for label, c in TOPICS:
        if c == code:
            return label
    return code


def get_confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Отправить", callback_data="appeal_confirm"),
            InlineKeyboardButton("❌ Отмена", callback_data="appeal_cancel"),
        ]
    ])


def format_appeal_preview(appeal_data: dict) -> str:
    topic = get_topic_label(appeal_data.get("topic", ""))
    name = appeal_data.get("name", "—")
    phone = appeal_data.get("phone", "—")
    description = appeal_data.get("description", "—")
    return (
        "📋 *Ваше обращение:*\n\n"
        f"👤 ФИО: {name}\n"
        f"📱 Телефон: {phone}\n"
        f"📂 Тема: {topic}\n"
        f"📝 Суть: {description}\n\n"
        "_Всё верно? Нажмите «Отправить» или «Отмена» для исправления._"
    )


def format_admin_message(appeal_data: dict, user) -> str:
    topic_code = appeal_data.get("topic", "other")
    topic = get_topic_label(topic_code)
    name = appeal_data.get("name", "—")
    phone = appeal_data.get("phone", "—")
    description = appeal_data.get("description", "—")
    now = datetime.now(MOSCOW_TZ).strftime("%d.%m.%Y %H:%M МСК")
    deputy = TOPIC_TO_DEPUTY.get(topic_code, TOPIC_TO_DEPUTY["other"])

    username = f"@{user.username}" if user.username else "нет username"
    tg_id = user.id

    return (
        "🆕 *НОВОЕ ОБРАЩЕНИЕ*\n"
        "━━━━━━━━━━━━━━━━━\n"
        f"👤 *ФИО:* {name}\n"
        f"📱 *Телефон:* {phone}\n"
        f"📂 *Тема:* {topic}\n"
        f"📋 *Суть:*\n{description}\n"
        "━━━━━━━━━━━━━━━━━\n"
        f"🎯 *Ответственный зам:* {deputy}\n"
        "━━━━━━━━━━━━━━━━━\n"
        f"🕐 {now}\n"
        f"📩 Telegram: {username} (ID: {tg_id})"
    )


async def send_appeal_to_admin(appeal_data: dict, user) -> bool:
    """Отправляет обращение в Telegram-группу сотрудников через admin-бота."""
    try:
        admin_bot = Bot(token=config.ADMIN_BOT_TOKEN)
        message = format_admin_message(appeal_data, user)
        await admin_bot.send_message(
            chat_id=config.ADMIN_GROUP_CHAT_ID,
            text=message,
            parse_mode="Markdown",
        )
        return True
    except Exception as e:
        logger.error(f"Ошибка при отправке обращения в группу: {e}")
        return False
