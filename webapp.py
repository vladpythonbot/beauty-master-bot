import hashlib
import hmac
import json
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import parse_qsl

from aiohttp import web
from aiogram import Bot

from data import SERVICES
from database import Database
from keyboards import admin_application_keyboard
from texts import admin_application_text
from texts import format_date


BASE_DIR = Path(__file__).resolve().parent
MINIAPP_DIR = BASE_DIR / "miniapp"
SITE_DIR = BASE_DIR / "site"


def _service_names(service_ids: list[str]) -> str:
    selected = [service for service in SERVICES if service["id"] in service_ids]
    return "\n".join(f"{service['name']} — {service['price']}" for service in selected)


def _valid_service_ids(service_ids: list[str]) -> list[str]:
    known_ids = {service["id"] for service in SERVICES}
    return [service_id for service_id in service_ids if service_id in known_ids]


def _is_admin_request(request: web.Request, user: dict | None) -> bool:
    if request.app["public_admin_mode"]:
        return True
    return bool(user and int(user["id"]) == request.app["admin_id"])


def _get_admin_user_from_request(request: web.Request) -> dict | None:
    user = _get_user_from_request(request, required=not request.app["public_admin_mode"])
    if not _is_admin_request(request, user):
        raise web.HTTPForbidden(text="Admin only")
    return user


def _parse_iso_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise web.HTTPBadRequest(text="date must be YYYY-MM-DD") from exc


def _parse_time_minutes(value: str) -> int:
    try:
        parsed = datetime.strptime(value, "%H:%M")
    except ValueError as exc:
        raise web.HTTPBadRequest(text="time must be HH:MM") from exc
    return parsed.hour * 60 + parsed.minute


def _format_time(minutes: int) -> str:
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def _build_schedule_slots(payload: dict) -> tuple[str, dict[str, list[str]]]:
    group_id = str(payload.get("group_id", "")).strip()
    start_date = _parse_iso_date(str(payload.get("start_date", "")))
    end_date = _parse_iso_date(str(payload.get("end_date", "")))
    weekdays = {int(day) for day in payload.get("weekdays", []) if str(day).isdigit()}
    start_minutes = _parse_time_minutes(str(payload.get("start_time", "")))
    end_minutes = _parse_time_minutes(str(payload.get("end_time", "")))
    step_minutes = int(payload.get("step_minutes") or 60)

    if not group_id or not weekdays:
        raise web.HTTPBadRequest(text="group_id and weekdays are required")
    if end_date < start_date:
        raise web.HTTPBadRequest(text="end_date must be after start_date")
    if (end_date - start_date).days > 90:
        raise web.HTTPBadRequest(text="schedule range is too long")
    if start_minutes >= end_minutes:
        raise web.HTTPBadRequest(text="start_time must be before end_time")
    if step_minutes not in {30, 45, 60, 90, 120}:
        raise web.HTTPBadRequest(text="step_minutes is invalid")
    if any(day < 0 or day > 6 for day in weekdays):
        raise web.HTTPBadRequest(text="weekdays are invalid")

    slots_by_date: dict[str, list[str]] = {}
    current = start_date
    while current <= end_date:
        if current.weekday() in weekdays:
            slots_by_date[current.isoformat()] = [
                _format_time(minutes)
                for minutes in range(start_minutes, end_minutes, step_minutes)
            ]
        current += timedelta(days=1)
    return group_id, slots_by_date


def _validate_init_data(init_data: str, bot_token: str) -> dict:
    parsed = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = parsed.pop("hash", "")
    if not received_hash:
        raise web.HTTPUnauthorized(text="Telegram initData hash is missing")

    data_check_string = "\n".join(f"{key}={value}" for key, value in sorted(parsed.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(calculated_hash, received_hash):
        raise web.HTTPUnauthorized(text="Telegram initData is invalid")

    user_raw = parsed.get("user", "{}")
    try:
        user = json.loads(user_raw)
    except json.JSONDecodeError as exc:
        raise web.HTTPUnauthorized(text="Telegram user payload is invalid") from exc

    if not user.get("id"):
        raise web.HTTPUnauthorized(text="Telegram user id is missing")
    return user


def _get_user_from_request(request: web.Request, required: bool = True) -> dict | None:
    init_data = request.headers.get("X-Telegram-Init-Data", "")
    if not init_data and required:
        raise web.HTTPUnauthorized(text="Telegram initData is required")
    if not init_data:
        return None
    return _validate_init_data(init_data, request.app["bot_token"])


async def miniapp_page(_: web.Request) -> web.FileResponse:
    return web.FileResponse(MINIAPP_DIR / "index.html")


async def site_page(_: web.Request) -> web.FileResponse:
    return web.FileResponse(SITE_DIR / "index.html")


async def api_bootstrap(request: web.Request) -> web.Response:
    user = _get_user_from_request(request, required=False)
    groups = await request.app["db"].get_schedule_groups()
    return web.json_response(
        {
            "services": SERVICES,
            "groups": groups,
            "is_admin": _is_admin_request(request, user),
        }
    )


async def api_dates(request: web.Request) -> web.Response:
    group_id = request.query.get("group_id", "")
    if not group_id:
        raise web.HTTPBadRequest(text="group_id is required")
    dates = await request.app["db"].get_available_dates(group_id)
    return web.json_response({"dates": dates})


async def api_times(request: web.Request) -> web.Response:
    group_id = request.query.get("group_id", "")
    slot_date = request.query.get("date", "")
    if not group_id or not slot_date:
        raise web.HTTPBadRequest(text="group_id and date are required")
    slots = await request.app["db"].get_available_slots(group_id, slot_date)
    return web.json_response({"slots": slots})


async def api_create_application(request: web.Request) -> web.Response:
    user = _get_user_from_request(request)
    payload = await request.json()

    service_ids = payload.get("service_ids") or []
    name = str(payload.get("name", "")).strip()
    contact = str(payload.get("contact", "")).strip()
    slot_id = int(payload.get("slot_id") or 0)

    if not service_ids or not name or not contact or not slot_id:
        raise web.HTTPBadRequest(text="service_ids, name, contact and slot_id are required")

    slot = await request.app["db"].get_slot(slot_id)
    if not slot or slot["status"] != "free":
        raise web.HTTPConflict(text="Slot is not available")

    service_text = _service_names(service_ids)
    if not service_text:
        raise web.HTTPBadRequest(text="Selected services are invalid")

    schedule_group = await request.app["db"].get_schedule_group(slot["group_id"])
    group_service_ids = set((schedule_group or {}).get("service_ids") or [])
    if not group_service_ids or not set(service_ids).issubset(group_service_ids):
        raise web.HTTPBadRequest(text="Selected master does not provide these services")

    application_id = await request.app["db"].create_application_for_slot(
        user_id=int(user["id"]),
        username=user.get("username"),
        client_name=name,
        service=service_text,
        contact=contact,
        slot_id=slot_id,
    )
    if not application_id:
        raise web.HTTPConflict(text="Slot is not available")

    data = {
        "service_ids": service_ids,
        "group_name": slot["group_name"],
        "slot_date": slot["slot_date"],
        "slot_time": slot["slot_time"],
        "name": name,
        "contact": contact,
    }
    await request.app["bot"].send_message(
        request.app["admin_id"],
        admin_application_text(application_id, int(user["id"]), user.get("username"), data),
        reply_markup=admin_application_keyboard(application_id),
    )
    await request.app["bot"].send_message(
        int(user["id"]),
        (
            "✅ Заявку отримано.\n\n"
            f"Послуга:\n{_service_names(service_ids)}\n\n"
            f"Майстер: {slot['group_name']}\n"
            f"Дата: {format_date(slot['slot_date'])}\n"
            f"Час: {slot['slot_time']}\n\n"
            "Майстер підтвердить запис окремим повідомленням."
        ),
    )
    return web.json_response({"ok": True, "application_id": application_id})


async def api_admin_slots(request: web.Request) -> web.Response:
    _get_admin_user_from_request(request)
    slots = await request.app["db"].get_upcoming_slots(limit=1000)
    return web.json_response({"slots": slots})


async def api_admin_create_group(request: web.Request) -> web.Response:
    _get_admin_user_from_request(request)

    payload = await request.json()
    name = str(payload.get("name", "")).strip()
    service_ids = _valid_service_ids(payload.get("service_ids") or [])
    if len(name) < 2:
        raise web.HTTPBadRequest(text="name is required")
    if not service_ids:
        raise web.HTTPBadRequest(text="service_ids are required")

    group = await request.app["db"].create_schedule_group(name, service_ids)
    return web.json_response({"ok": True, "group": group})


async def api_admin_update_group(request: web.Request) -> web.Response:
    _get_admin_user_from_request(request)

    group_id = request.match_info["group_id"]
    payload = await request.json()
    name = str(payload.get("name", "")).strip()
    service_ids = _valid_service_ids(payload.get("service_ids") or [])
    if len(name) < 2:
        raise web.HTTPBadRequest(text="name is required")
    if not service_ids:
        raise web.HTTPBadRequest(text="service_ids are required")

    updated = await request.app["db"].update_schedule_group(group_id, name, service_ids)
    if not updated:
        raise web.HTTPNotFound(text="Group not found")
    return web.json_response({"ok": True})


async def api_admin_delete_group(request: web.Request) -> web.Response:
    _get_admin_user_from_request(request)

    group_id = request.match_info["group_id"]
    deleted, message = await request.app["db"].delete_schedule_group(group_id)
    if not deleted:
        return web.json_response({"ok": False, "message": message}, status=409)
    return web.json_response({"ok": True})


async def api_admin_applications(request: web.Request) -> web.Response:
    _get_admin_user_from_request(request)
    applications = await request.app["db"].get_recent_applications(limit=30)
    return web.json_response({"applications": applications})


async def api_admin_update_application(request: web.Request) -> web.Response:
    _get_admin_user_from_request(request)

    application_id = int(request.match_info["application_id"])
    payload = await request.json()
    status = payload.get("status")
    if status not in {"confirmed", "cancelled"}:
        raise web.HTTPBadRequest(text="status must be confirmed or cancelled")

    application = await request.app["db"].update_status(application_id, status)
    if not application:
        raise web.HTTPNotFound(text="Application not found")

    if status == "confirmed":
        text = (
            "✅ Ваш запис підтверджено.\n\n"
            f"Дата: {format_date(application['desired_date'])}\n"
            f"Час: {application['desired_time']}\n"
            f"Майстер: {application['schedule_group'] or 'майстер'}"
        )
    else:
        text = "❌ На жаль, заявку скасовано. Обраний час знову доступний для запису."

    await request.app["bot"].send_message(application["user_id"], text)
    return web.json_response({"ok": True, "application": application})


async def api_admin_add_slots(request: web.Request) -> web.Response:
    _get_admin_user_from_request(request)

    payload = await request.json()
    group_id = str(payload.get("group_id", "")).strip()
    slot_date = str(payload.get("slot_date", "")).strip()
    slot_dates = [str(item).strip() for item in payload.get("slot_dates", []) if str(item).strip()]
    times = payload.get("times") or []
    if slot_date and slot_date not in slot_dates:
        slot_dates.append(slot_date)
    if not group_id or not slot_dates or not times:
        raise web.HTTPBadRequest(text="group_id, slot_dates and times are required")
    if len(slot_dates) > 31:
        raise web.HTTPBadRequest(text="too many dates")

    valid_dates = sorted({_parse_iso_date(date_value).isoformat() for date_value in slot_dates})
    valid_times = sorted({_format_time(_parse_time_minutes(str(time))) for time in times})
    slots_by_date = {date_value: valid_times for date_value in valid_dates}
    created = await request.app["db"].add_slots_bulk(group_id, slots_by_date)
    planned = len(valid_dates) * len(valid_times)
    return web.json_response({"ok": True, "created": created, "planned": planned})


async def api_admin_add_slots_bulk(request: web.Request) -> web.Response:
    _get_admin_user_from_request(request)

    payload = await request.json()
    group_id, slots_by_date = _build_schedule_slots(payload)
    if not slots_by_date:
        raise web.HTTPBadRequest(text="schedule has no dates")

    created = await request.app["db"].add_slots_bulk(group_id, slots_by_date)
    planned = sum(len(times) for times in slots_by_date.values())
    return web.json_response({"ok": True, "created": created, "planned": planned})


async def api_admin_delete_slot(request: web.Request) -> web.Response:
    _get_admin_user_from_request(request)

    slot_id = int(request.match_info["slot_id"])
    deleted = await request.app["db"].delete_slot(slot_id)
    return web.json_response({"ok": deleted})


def create_web_app(db: Database, bot: Bot, bot_token: str, admin_id: int, public_admin_mode: bool = False) -> web.Application:
    app = web.Application()
    app["db"] = db
    app["bot"] = bot
    app["bot_token"] = bot_token
    app["admin_id"] = admin_id
    app["public_admin_mode"] = public_admin_mode

    app.router.add_get("/", site_page)
    app.router.add_get("/miniapp", miniapp_page)
    app.router.add_get("/miniapp/", miniapp_page)
    app.router.add_get("/api/bootstrap", api_bootstrap)
    app.router.add_get("/api/dates", api_dates)
    app.router.add_get("/api/times", api_times)
    app.router.add_post("/api/applications", api_create_application)
    app.router.add_get("/api/admin/slots", api_admin_slots)
    app.router.add_post("/api/admin/slots", api_admin_add_slots)
    app.router.add_post("/api/admin/slots/bulk", api_admin_add_slots_bulk)
    app.router.add_delete("/api/admin/slots/{slot_id}", api_admin_delete_slot)
    app.router.add_post("/api/admin/groups", api_admin_create_group)
    app.router.add_patch("/api/admin/groups/{group_id}", api_admin_update_group)
    app.router.add_delete("/api/admin/groups/{group_id}", api_admin_delete_group)
    app.router.add_get("/api/admin/applications", api_admin_applications)
    app.router.add_patch("/api/admin/applications/{application_id}", api_admin_update_application)
    app.router.add_static("/miniapp/static", MINIAPP_DIR, show_index=False)
    app.router.add_static("/", SITE_DIR, show_index=False)
    return app
