from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, WebAppInfo


def main_menu(mini_app_url: str = "") -> ReplyKeyboardMarkup:
    booking_button = KeyboardButton(text="Відкрити Mini App")
    if mini_app_url:
        booking_button = KeyboardButton(text="Відкрити Mini App", web_app=WebAppInfo(url=mini_app_url))

    return ReplyKeyboardMarkup(
        keyboard=[[booking_button]],
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
