import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = str(BASE_DIR / "beauty_bot.db")


def normalize_db_path(value: str) -> str:
    path = Path(value.strip() or DEFAULT_DB_PATH).expanduser()
    if path.is_absolute():
        return str(path)
    return str(BASE_DIR / path)


def normalize_mini_app_url(value: str) -> str:
    url = value.strip().rstrip("/")
    if not url:
        return ""
    if url.endswith("/miniapp"):
        return url
    return f"{url}/miniapp"


@dataclass(frozen=True)
class Config:
    bot_token: str
    admin_id: int
    db_path: str = DEFAULT_DB_PATH
    mini_app_url: str = ""
    public_admin_mode: bool = False
    host: str = "0.0.0.0"
    port: int = 8000


def load_config() -> Config:
    token = os.getenv("BOT_TOKEN", "").strip()
    admin_id = os.getenv("ADMIN_ID", "").strip()
    db_path = normalize_db_path(os.getenv("DB_PATH", DEFAULT_DB_PATH))
    mini_app_url = os.getenv("MINI_APP_URL", "").strip()
    public_admin_mode = os.getenv("PUBLIC_ADMIN_MODE", "false").strip().lower() in {"1", "true", "yes", "on"}
    railway_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN", "").strip()
    host = os.getenv("HOST", "0.0.0.0").strip()
    port = int(os.getenv("PORT", "8000"))

    if not token:
        raise RuntimeError("BOT_TOKEN is not set in .env")
    if not admin_id.isdigit():
        raise RuntimeError("ADMIN_ID must be a number in .env")

    if not mini_app_url and railway_domain:
        mini_app_url = f"https://{railway_domain}/miniapp"
    else:
        mini_app_url = normalize_mini_app_url(mini_app_url)

    return Config(
        bot_token=token,
        admin_id=int(admin_id),
        db_path=db_path,
        mini_app_url=mini_app_url,
        public_admin_mode=public_admin_mode,
        host=host,
        port=port,
    )
