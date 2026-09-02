from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, WebAppInfo


def mini_app_url_with_mode(mini_app_url: str, mode: str) -> str:
    separator = "&" if "?" in mini_app_url else "?"
    return f"{mini_app_url}{separator}mode={mode}"


def main_menu(mini_app_url: str = "", is_admin: bool = False) -> ReplyKeyboardMarkup:
    booking_button = KeyboardButton(text="Відкрити Mini App")
    if mini_app_url:
        booking_button = KeyboardButton(text="Відкрити Mini App", web_app=WebAppInfo(url=mini_app_url))

    keyboard = [[booking_button]]
    if is_admin:
        admin_button = KeyboardButton(text="Адмін-панель")
        if mini_app_url:
            admin_button = KeyboardButton(
                text="Адмін-панель",
                web_app=WebAppInfo(url=mini_app_url_with_mode(mini_app_url, "admin")),
            )
        keyboard.append([admin_button])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Відкрийте Mini App",
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
