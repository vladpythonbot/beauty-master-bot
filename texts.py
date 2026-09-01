from html import escape

from data import SERVICES
from keyboards import format_date, format_date_short


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
        "\n\nОберіть одну або кілька послуг."
        f"{selected_line}"
    )


def application_summary(data: dict) -> str:
    return (
        "📝 <b>Перевірте заявку</b>\n\n"
        f"Послуги:\n{format_selected_services(data['service_ids'])}\n"
        f"Адреса/майстер: <b>{escape(data['group_name'])}</b>\n"
        f"Дата: <b>{format_date(data['slot_date'])}</b>\n"
        f"Час: <b>{escape(data['slot_time'])}</b>\n"
        f"Ім'я: <b>{escape(data['name'])}</b>\n"
        f"Контакт: <b>{escape(data['contact'])}</b>\n\n"
        "Майстер підтвердить запис окремим повідомленням."
    )


def admin_application_text(application_id: int, user_id: int, username: str | None, data: dict) -> str:
    username_text = f"@{escape(username)}" if username else "не вказано"
    return (
        "🔔 <b>Нова заявка на запис</b>\n\n"
        f"ID заявки: <b>{application_id}</b>\n"
        f"Telegram ID: <code>{user_id}</code>\n"
        f"Username: {username_text}\n\n"
        f"Послуги:\n{format_selected_services(data['service_ids'])}\n"
        f"Адреса/майстер: <b>{escape(data['group_name'])}</b>\n"
        f"Дата: <b>{format_date(data['slot_date'])}</b>\n"
        f"Час: <b>{escape(data['slot_time'])}</b>\n"
        f"Ім'я: <b>{escape(data['name'])}</b>\n"
        f"Контакт: <b>{escape(data['contact'])}</b>\n\n"
        "Підтвердіть або скасуйте заявку."
    )


def admin_applications_text(applications: list[dict]) -> str:
    if not applications:
        return "Заявок поки немає."

    status_names = {
        "new": "очікує",
        "confirmed": "підтверджено",
        "cancelled": "скасовано",
    }
    lines = ["📝 <b>Останні заявки</b>", ""]
    for item in applications:
        lines.append(
            f"#{item['id']} · {escape(item['desired_date'])} {escape(item['desired_time'])} · "
            f"{escape(item['client_name'])} · {escape(status_names.get(item['status'], item['status']))}"
        )
        lines.append(f"{escape(item['service'])}")
        lines.append("")
    return "\n".join(lines).strip()


def admin_slots_text(slots: list[dict]) -> str:
    if not slots:
        return "Вільних вікон поки немає."

    status_names = {"free": "вільно", "blocked": "очікує", "booked": "записано"}
    grouped: dict[str, dict[str, list[dict]]] = {}
    for slot in slots:
        grouped.setdefault(slot["group_name"], {}).setdefault(slot["slot_date"], []).append(slot)

    lines = ["📅 <b>Вільні вікна</b>", ""]
    for group_name, dates in grouped.items():
        lines.append(f"<b>{escape(group_name)}</b>")
        for slot_date, day_slots in dates.items():
            time_items = [
                f"{escape(slot['slot_time'])} ({status_names.get(slot['status'], slot['status'])})"
                for slot in day_slots
            ]
            lines.append(f"• {format_date_short(slot_date)}: {', '.join(time_items)}")
        lines.append("")

    lines.append("Кнопки нижче показані тільки для вільних вікон: натисніть час, щоб змінити, або «Видалити».")
    return "\n".join(lines).strip()
