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


def is_railway() -> bool:
    return bool(os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RAILWAY_PUBLIC_DOMAIN"))


def validate_db_path_for_runtime(db_path: str) -> None:
    if is_railway() and not Path(db_path).as_posix().startswith("/data/"):
        raise RuntimeError(
            "Railway SQLite must use a persistent Volume. "
            "Set DB_PATH=/data/beauty_bot.db in Railway Variables."
        )


@dataclass(frozen=True)
class Config:
    bot_token: str
    admin_id: int
    db_path: str = DEFAULT_DB_PATH
    mini_app_url: str = ""
    support_username: str = ""
    public_admin_mode: bool = False
    host: str = "0.0.0.0"
    port: int = 8000


def load_config() -> Config:
    token = os.getenv("BOT_TOKEN", "").strip()
    admin_id = os.getenv("ADMIN_ID", "").strip()
    db_path = normalize_db_path(os.getenv("DB_PATH", DEFAULT_DB_PATH))
    mini_app_url = os.getenv("MINI_APP_URL", "").strip()
    support_username = os.getenv("SUPPORT_USERNAME", "").strip().lstrip("@")
    public_admin_mode = os.getenv("PUBLIC_ADMIN_MODE", "false").strip().lower() in {"1", "true", "yes", "on"}
    railway_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN", "").strip()
    host = os.getenv("HOST", "0.0.0.0").strip()
    port = int(os.getenv("PORT", "8000"))

    if not token:
        raise RuntimeError("BOT_TOKEN is not set in .env")
    if not admin_id.isdigit():
        raise RuntimeError("ADMIN_ID must be a number in .env")
    validate_db_path_for_runtime(db_path)

    if not mini_app_url and railway_domain:
        mini_app_url = f"https://{railway_domain}/miniapp"
    else:
        mini_app_url = normalize_mini_app_url(mini_app_url)

    return Config(
        bot_token=token,
        admin_id=int(admin_id),
        db_path=db_path,
        mini_app_url=mini_app_url,
        support_username=support_username,
        public_admin_mode=public_admin_mode,
        host=host,
        port=port,
    )
