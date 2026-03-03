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


async def run_health_server(port: int):
    """Минимальный HTTP-сервер для Render.com health check."""
    async def health(request):
        return web.Response(text="OK")

    http_app = web.Application()
    http_app.router.add_get("/", health)
    http_app.router.add_get("/health", health)

    runner = web.AppRunner(http_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    return runner


async def main():
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("Запуск бота «Справочная Коломны»...")
    config.display()

    await init_db()
    logger.info("База данных инициализирована.")

    # На Render запускаем health-check сервер чтобы сервис не помечался как упавший
    port = int(os.getenv("PORT", 0))
    if port:
        runner = await run_health_server(port)
        logger.info(f"Health-check сервер запущен на порту {port}")
    else:
        runner = None

    app = Application.builder().token(config.CITIZEN_BOT_TOKEN).build()
    setup_application(app)

    logger.info("Бот запущен в polling-режиме...")
    try:
        await app.run_polling(
            allowed_updates=["message", "callback_query"],
            drop_pending_updates=True,
        )
    finally:
        if runner:
            await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
