import logging
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


def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Запуск бота «Справочная Коломны»...")
    config.display()

    async def on_startup(application: Application) -> None:
        await init_db()
        logger.info("База данных инициализирована.")

    app = (
        Application.builder()
        .token(config.CITIZEN_BOT_TOKEN)
        .post_init(on_startup)
        .build()
    )
    setup_application(app)

    logger.info("Бот запущен (polling).")
    app.run_polling(
        allowed_updates=["message", "callback_query"],
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()
