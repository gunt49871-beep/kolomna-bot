import re
import logging
from openai import AsyncOpenAI
from src.config import config
from src.knowledge_base import SYSTEM_PROMPT

logger = logging.getLogger(__name__)

_client = AsyncOpenAI(
    api_key=config.GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1",
)


async def get_ai_response(history: list, user_message: str) -> tuple[str, bool]:
    """
    Отправляет запрос к Groq (llama-3.3-70b) и возвращает (текст_ответа, suggest_appeal).
    suggest_appeal=True если бот не смог дать исчерпывающий ответ.
    """
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    try:
        response = await _client.chat.completions.create(
            model=config.GROQ_MODEL,
            messages=messages,
            temperature=0.3,
            max_tokens=1024,
        )
        raw = response.choices[0].message.content or ""
    except Exception as e:
        logger.error(f"Ошибка AI API: {e}")
        return (
            "Извините, произошла техническая ошибка. Попробуйте ещё раз или оставьте обращение через кнопку ниже.",
            True,
        )

    suggest_appeal = _extract_suggest_appeal(raw)
    clean_text = _strip_json_marker(raw)
    return clean_text, suggest_appeal


def _extract_suggest_appeal(text: str) -> bool:
    match = re.search(r'\{"suggest_appeal":\s*(true|false)\}', text, re.IGNORECASE)
    if match:
        return match.group(1).lower() == "true"
    return False


def _strip_json_marker(text: str) -> str:
    cleaned = re.sub(r'\s*\{"suggest_appeal":\s*(true|false)\}\s*', "", text, flags=re.IGNORECASE)
    return cleaned.strip()
