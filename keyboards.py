from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from data import SERVICES


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Записатися")],
            [KeyboardButton(text="Послуги"), KeyboardButton(text="Портфоліо")],
            [KeyboardButton(text="Інфо")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Оберіть дію",
    )


def cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Скасувати")],
        ],
        resize_keyboard=True,
    )


def service_choice_keyboard(selected_ids: list[str] | None = None) -> InlineKeyboardMarkup:
    selected = set(selected_ids or [])
    keyboard = []

    for service in SERVICES:
        mark = "✅" if service["id"] in selected else "▫️"
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=f"{mark} {service['name']} · {service['price']}",
                    callback_data=f"service_toggle:{service['id']}",
                )
            ]
        )

    keyboard.append([InlineKeyboardButton(text="Готово", callback_data="service_done")])
    keyboard.append([InlineKeyboardButton(text="Скасувати", callback_data="client_cancel")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def application_summary_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Підтвердити", callback_data="client_confirm"),
                InlineKeyboardButton(text="Змінити", callback_data="client_change"),
            ],
            [InlineKeyboardButton(text="Скасувати", callback_data="client_cancel")],
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
