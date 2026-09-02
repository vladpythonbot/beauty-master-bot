from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo


def mini_app_url_with_mode(mini_app_url: str, mode: str) -> str:
    separator = "&" if "?" in mini_app_url else "?"
    return f"{mini_app_url}{separator}mode={mode}"


def main_menu(mini_app_url: str = "", is_admin: bool = False) -> InlineKeyboardMarkup | None:
    if not mini_app_url:
        return None

    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Відкрити запис", web_app=WebAppInfo(url=mini_app_url))]]
    )


def admin_menu(mini_app_url: str = "") -> InlineKeyboardMarkup | None:
    if not mini_app_url:
        return None

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Відкрити адмінку",
                    web_app=WebAppInfo(url=mini_app_url_with_mode(mini_app_url, "admin")),
                )
            ]
        ]
    )


def admin_application_keyboard(application_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Підтвердити",
                    callback_data=f"admin_confirm:{application_id}",
                ),
                InlineKeyboardButton(
                    text="Скасувати",
                    callback_data=f"admin_cancel:{application_id}",
                ),
            ]
        ]
    )


def format_date(value: str) -> str:
    year, month, day = value.split("-")
    return f"{day}.{month}.{year}"
