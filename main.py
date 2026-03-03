import asyncio
import logging
import os
import colorlog
from telegram.ext import Application
from src.config import config
from src.state_manager import init_db
from src.bot_handlers import setup_application


def setup_logging():
    handler = colorlog.StreamHandler()
    handler.setFormatter(colorlog.ColoredFormatter(
        "%(log_color)s%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "bold_red",
        },
    ))
    logging.basicConfig(level=logging.INFO, handlers=[handler])
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.WARNING)


async def main():
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("Запуск бота «Справочная Коломны»...")
    config.display()

    await init_db()
    logger.info("База данных инициализирована.")

    app = Application.builder().token(config.CITIZEN_BOT_TOKEN).build()
    setup_application(app)

    webhook_url = os.getenv("WEBHOOK_URL", "")

    if webhook_url:
        # Продакшн: webhook-режим (Render.com, любой сервер с HTTPS)
        port = int(os.getenv("PORT", 8080))
        logger.info(f"Запуск в webhook-режиме: {webhook_url} (порт {port})")
        await app.run_webhook(
            listen="0.0.0.0",
            port=port,
            webhook_url=webhook_url,
            allowed_updates=["message", "callback_query"],
            drop_pending_updates=True,
        )
    else:
        # Локально: polling-режим (для разработки и тестирования)
        logger.info("Запуск в polling-режиме (локально)...")
        await app.run_polling(
            allowed_updates=["message", "callback_query"],
            drop_pending_updates=True,
        )


if __name__ == "__main__":
    asyncio.run(main())
