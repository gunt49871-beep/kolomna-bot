import asyncio
import logging
import os
import colorlog
from aiohttp import web
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

    # Health-check сервер для Render.com (запускается в том же event loop — нет race condition)
    port = int(os.getenv("PORT", 0))
    if port:
        http_app = web.Application()

        async def health(request):
            return web.Response(text="OK")

        http_app.router.add_get("/", health)
        http_app.router.add_get("/health", health)
        runner = web.AppRunner(http_app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", port)
        await site.start()
        logger.info(f"Health-check сервер запущен на порту {port}")

    # Telegram бот
    app = Application.builder().token(config.CITIZEN_BOT_TOKEN).build()
    setup_application(app)

    async with app:
        await app.start()
        await app.updater.start_polling(
            allowed_updates=["message", "callback_query"],
            drop_pending_updates=True,
        )
        logger.info("Бот запущен.")
        await asyncio.sleep(float("inf"))


if __name__ == "__main__":
    asyncio.run(main())
