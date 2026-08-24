from html import escape

from data import SERVICES
from keyboards import format_date


def get_service(service_id: str) -> dict | None:
    return next((service for service in SERVICES if service["id"] == service_id), None)


def format_selected_services(service_ids: list[str]) -> str:
    items = []
    for service_id in service_ids:
        service = get_service(service_id)
        if service:
            items.append(f"{service['name']} — {service['price']}")
    return "\n".join(f"• {escape(item)}" for item in items)


def services_text() -> str:
    lines = ["💅 <b>Послуги та ціни</b>", ""]
    for service in SERVICES:
        lines.append(f"• {escape(service['name'])} — <b>{escape(service['price'])}</b>")
    return "\n".join(lines)


def booking_services_text(selected_ids: list[str] | None = None) -> str:
    selected_count = len(selected_ids or [])
    selected_line = f"\n\nОбрано: <b>{selected_count}</b>" if selected_count else ""
    return (
        f"{services_text()}"
        "\n\nОберіть одну або кілька послуг кнопками нижче."
        f"{selected_line}"
    )


def application_summary(data: dict) -> str:
    return (
        "📝 <b>Перевірте заявку</b>\n\n"
        f"Ім'я: <b>{escape(data['name'])}</b>\n"
        f"Послуги:\n{format_selected_services(data['service_ids'])}\n"
        f"Адреса/майстер: <b>{escape(data['group_name'])}</b>\n"
        f"Дата: <b>{format_date(data['slot_date'])}</b>\n"
        f"Час: <b>{escape(data['slot_time'])}</b>\n"
        f"Контакт: <b>{escape(data['contact'])}</b>\n\n"
        "Після підтвердження заявки майстром цей час буде остаточно закріплено за вами."
    )


def admin_application_text(application_id: int, user_id: int, username: str | None, data: dict) -> str:
    username_text = f"@{escape(username)}" if username else "не вказано"
    return (
        "🔔 <b>Нова заявка на запис</b>\n\n"
        f"ID заявки: <b>{application_id}</b>\n"
        f"Telegram ID: <code>{user_id}</code>\n"
        f"Username: {username_text}\n\n"
        f"Ім'я: <b>{escape(data['name'])}</b>\n"
        f"Послуги:\n{format_selected_services(data['service_ids'])}\n"
        f"Адреса/майстер: <b>{escape(data['group_name'])}</b>\n"
        f"Дата: <b>{format_date(data['slot_date'])}</b>\n"
        f"Час: <b>{escape(data['slot_time'])}</b>\n"
        f"Контакт: <b>{escape(data['contact'])}</b>\n\n"
        "Підтвердіть або скасуйте заявку. До рішення майстра час тимчасово заблоковано."
    )
