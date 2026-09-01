import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Config:
    bot_token: str
    admin_id: int
    db_path: str = "beauty_bot.db"
    mini_app_url: str = ""
    host: str = "0.0.0.0"
    port: int = 8000


def load_config() -> Config:
    token = os.getenv("BOT_TOKEN", "").strip()
    admin_id = os.getenv("ADMIN_ID", "").strip()
    db_path = os.getenv("DB_PATH", "beauty_bot.db").strip()
    mini_app_url = os.getenv("MINI_APP_URL", "").strip()
    railway_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN", "").strip()
    host = os.getenv("HOST", "0.0.0.0").strip()
    port = int(os.getenv("PORT", "8000"))

    if not token:
        raise RuntimeError("BOT_TOKEN is not set in .env")
    if not admin_id.isdigit():
        raise RuntimeError("ADMIN_ID must be a number in .env")

    if not mini_app_url and railway_domain:
        mini_app_url = f"https://{railway_domain}/miniapp"

    return Config(
        bot_token=token,
        admin_id=int(admin_id),
        db_path=db_path,
        mini_app_url=mini_app_url,
        host=host,
        port=port,
    )
