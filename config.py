import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Config:
    bot_token: str
    admin_id: int
    db_path: str = "beauty_bot.db"


def load_config() -> Config:
    token = os.getenv("BOT_TOKEN", "").strip()
    admin_id = os.getenv("ADMIN_ID", "").strip()
    db_path = os.getenv("DB_PATH", "beauty_bot.db").strip()

    if not token:
        raise RuntimeError("BOT_TOKEN is not set in .env")
    if not admin_id.isdigit():
        raise RuntimeError("ADMIN_ID must be a number in .env")

    return Config(bot_token=token, admin_id=int(admin_id), db_path=db_path)
