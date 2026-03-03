import asyncio
import logging
import os
import threading
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


def start_health_server(port: int):
    """Health-check сервер в отдельном потоке — нужен для Render.com."""
    async def health(request):
        return web.Response(text="OK")

    async def run():
        http_app = web.Application()
        http_app.router.add_get("/", health)
        http_app.router.add_get("/health", health)
        runner = web.AppRunner(http_app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", port)
        await site.start()
        logging.getLogger(__name__).info(f"Health-check сервер запущен на порту {port}")
        await asyncio.sleep(float("inf"))  # крутимся вечно

    loop = asyncio.new_event_loop()
    thread = threading.Thread(
        target=loop.run_until_complete, args=(run(),), daemon=True
    )
    thread.start()


def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Запуск бота «Справочная Коломны»...")
    config.display()

    # Инициализируем БД синхронно
    asyncio.run(init_db())
    logger.info("База данных инициализирована.")

    # На Render запускаем health-check сервер в фоне
    port = int(os.getenv("PORT", 0))
    if port:
        start_health_server(port)

    # Запускаем Telegram бота (run_polling управляет своим event loop)
    app = Application.builder().token(config.CITIZEN_BOT_TOKEN).build()
    setup_application(app)

    logger.info("Бот запущен.")
    app.run_polling(
        allowed_updates=["message", "callback_query"],
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()
