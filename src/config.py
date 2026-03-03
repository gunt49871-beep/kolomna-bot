import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    CITIZEN_BOT_TOKEN: str = ""
    ADMIN_BOT_TOKEN: str = ""
    ADMIN_GROUP_CHAT_ID: str = ""
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    def __init__(self):
        self.CITIZEN_BOT_TOKEN = os.getenv("CITIZEN_BOT_TOKEN", "")
        self.ADMIN_BOT_TOKEN = os.getenv("ADMIN_BOT_TOKEN", "")
        self.ADMIN_GROUP_CHAT_ID = os.getenv("ADMIN_GROUP_CHAT_ID", "")
        self.GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
        self.GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        self._validate()

    def _validate(self):
        missing = []
        if not self.CITIZEN_BOT_TOKEN:
            missing.append("CITIZEN_BOT_TOKEN")
        if not self.ADMIN_BOT_TOKEN:
            missing.append("ADMIN_BOT_TOKEN")
        if not self.ADMIN_GROUP_CHAT_ID:
            missing.append("ADMIN_GROUP_CHAT_ID")
        if not self.GROQ_API_KEY:
            missing.append("GROQ_API_KEY")
        if missing:
            raise ValueError(
                f"Отсутствуют обязательные переменные окружения: {', '.join(missing)}\n"
                f"Скопируйте .env.example в .env и заполните значения."
            )

    def display(self):
        print(f"  CITIZEN_BOT_TOKEN: ...{self.CITIZEN_BOT_TOKEN[-6:]}")
        print(f"  ADMIN_BOT_TOKEN:   ...{self.ADMIN_BOT_TOKEN[-6:]}")
        print(f"  ADMIN_GROUP_CHAT_ID: {self.ADMIN_GROUP_CHAT_ID}")
        print(f"  GROQ_MODEL: {self.GROQ_MODEL}")


config = Config()
