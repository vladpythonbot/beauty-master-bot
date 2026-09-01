from datetime import datetime, timedelta

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from data import SERVICES


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Записатися")],
            [KeyboardButton(text="Послуги"), KeyboardButton(text="Портфоліо")],
            [KeyboardButton(text="Контакти")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Оберіть дію",
    )


def cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Скасувати")]],
        resize_keyboard=True,
    )


def admin_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Додати вікна", callback_data="admin_add_slots")],
            [InlineKeyboardButton(text="📅 Вільні вікна", callback_data="admin_list_slots")],
            [InlineKeyboardButton(text="📝 Заявки", callback_data="admin_list_applications")],
        ]
    )


def schedule_group_keyboard(groups: list[dict], prefix: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=group["name"], callback_data=f"{prefix}:{group['id']}")]
            for group in groups
        ]
    )


def admin_date_keyboard() -> InlineKeyboardMarkup:
    today = datetime.now().date()
    options = [
        ("Сьогодні", today),
        ("Завтра", today + timedelta(days=1)),
        ("+2 дні", today + timedelta(days=2)),
        ("+3 дні", today + timedelta(days=3)),
    ]
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=label, callback_data=f"admin_date:{date.isoformat()}")
                for label, date in options[:2]
            ],
            [
                InlineKeyboardButton(text=label, callback_data=f"admin_date:{date.isoformat()}")
                for label, date in options[2:]
            ],
            [InlineKeyboardButton(text="Ввести дату вручну", callback_data="admin_date_manual")],
            [InlineKeyboardButton(text="Скасувати", callback_data="client_cancel")],
        ]
    )


def admin_time_presets_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Ранок", callback_data="admin_times:morning"),
                InlineKeyboardButton(text="День", callback_data="admin_times:day"),
            ],
            [
                InlineKeyboardButton(text="Вечір", callback_data="admin_times:evening"),
                InlineKeyboardButton(text="Весь день", callback_data="admin_times:all"),
            ],
            [InlineKeyboardButton(text="Ввести час вручну", callback_data="admin_times_manual")],
            [InlineKeyboardButton(text="Скасувати", callback_data="client_cancel")],
        ]
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


def available_dates_keyboard(dates: list[str]) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text=format_date(date), callback_data=f"book_date:{date}")]
        for date in dates
    ]
    keyboard.append([InlineKeyboardButton(text="Скасувати", callback_data="client_cancel")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def available_times_keyboard(slots: list[dict]) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text=slot["slot_time"], callback_data=f"book_slot:{slot['id']}")]
        for slot in slots
    ]
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


def admin_slots_keyboard(slots: list[dict]) -> InlineKeyboardMarkup:
    keyboard = []
    for slot in slots:
        if slot["status"] == "free":
            label = f"{format_date_short(slot['slot_date'])} {slot['slot_time']} · {slot['group_name']}"
            keyboard.append(
                [
                    InlineKeyboardButton(text=label, callback_data=f"admin_edit_slot:{slot['id']}"),
                    InlineKeyboardButton(text="Видалити", callback_data=f"admin_delete_slot:{slot['id']}"),
                ]
            )
    keyboard.append([InlineKeyboardButton(text="➕ Додати вікна", callback_data="admin_add_slots")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def admin_application_list_keyboard(applications: list[dict]) -> InlineKeyboardMarkup:
    keyboard = []
    for application in applications:
        if application["status"] == "new":
            keyboard.append(
                [
                    InlineKeyboardButton(
                        text=f"Підтвердити #{application['id']}",
                        callback_data=f"admin_confirm:{application['id']}",
                    ),
                    InlineKeyboardButton(
                        text=f"Скасувати #{application['id']}",
                        callback_data=f"admin_cancel:{application['id']}",
                    ),
                ]
            )
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def format_date(value: str) -> str:
    year, month, day = value.split("-")
    return f"{day}.{month}.{year}"


def format_date_short(value: str) -> str:
    _, month, day = value.split("-")
    return f"{day}.{month}"
