import hashlib
import hmac
import json
from pathlib import Path
from urllib.parse import parse_qsl

from aiohttp import web
from aiogram import Bot

from data import SERVICES
from database import Database
from keyboards import admin_application_keyboard
from texts import admin_application_text


BASE_DIR = Path(__file__).resolve().parent
MINIAPP_DIR = BASE_DIR / "miniapp"
SITE_DIR = BASE_DIR / "site"


def _service_names(service_ids: list[str]) -> str:
    selected = [service for service in SERVICES if service["id"] in service_ids]
    return "\n".join(f"{service['name']} — {service['price']}" for service in selected)


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
            "is_admin": bool(user and int(user["id"]) == request.app["admin_id"]),
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
    return web.json_response({"ok": True, "application_id": application_id})


async def api_admin_slots(request: web.Request) -> web.Response:
    user = _get_user_from_request(request)
    if int(user["id"]) != request.app["admin_id"]:
        raise web.HTTPForbidden(text="Admin only")
    slots = await request.app["db"].get_upcoming_slots(limit=100)
    return web.json_response({"slots": slots})


async def api_admin_applications(request: web.Request) -> web.Response:
    user = _get_user_from_request(request)
    if int(user["id"]) != request.app["admin_id"]:
        raise web.HTTPForbidden(text="Admin only")
    applications = await request.app["db"].get_recent_applications(limit=30)
    return web.json_response({"applications": applications})


async def api_admin_update_application(request: web.Request) -> web.Response:
    user = _get_user_from_request(request)
    if int(user["id"]) != request.app["admin_id"]:
        raise web.HTTPForbidden(text="Admin only")

    application_id = int(request.match_info["application_id"])
    payload = await request.json()
    status = payload.get("status")
    if status not in {"confirmed", "cancelled"}:
        raise web.HTTPBadRequest(text="status must be confirmed or cancelled")

    application = await request.app["db"].update_status(application_id, status)
    if not application:
        raise web.HTTPNotFound(text="Application not found")

    if status == "confirmed":
        text = "✅ Ваш запис підтверджено. Майстер очікує вас у зазначений час."
    else:
        text = "❌ На жаль, заявку скасовано. Обраний час знову доступний для запису."

    await request.app["bot"].send_message(application["user_id"], text)
    return web.json_response({"ok": True, "application": application})


async def api_admin_add_slots(request: web.Request) -> web.Response:
    user = _get_user_from_request(request)
    if int(user["id"]) != request.app["admin_id"]:
        raise web.HTTPForbidden(text="Admin only")

    payload = await request.json()
    group_id = str(payload.get("group_id", "")).strip()
    slot_date = str(payload.get("slot_date", "")).strip()
    times = payload.get("times") or []
    if not group_id or not slot_date or not times:
        raise web.HTTPBadRequest(text="group_id, slot_date and times are required")

    created = await request.app["db"].add_slots(group_id, slot_date, times)
    return web.json_response({"ok": True, "created": created})


async def api_admin_delete_slot(request: web.Request) -> web.Response:
    user = _get_user_from_request(request)
    if int(user["id"]) != request.app["admin_id"]:
        raise web.HTTPForbidden(text="Admin only")

    slot_id = int(request.match_info["slot_id"])
    deleted = await request.app["db"].delete_slot(slot_id)
    return web.json_response({"ok": deleted})


def create_web_app(db: Database, bot: Bot, bot_token: str, admin_id: int) -> web.Application:
    app = web.Application()
    app["db"] = db
    app["bot"] = bot
    app["bot_token"] = bot_token
    app["admin_id"] = admin_id

    app.router.add_get("/", site_page)
    app.router.add_get("/miniapp", miniapp_page)
    app.router.add_get("/miniapp/", miniapp_page)
    app.router.add_get("/api/bootstrap", api_bootstrap)
    app.router.add_get("/api/dates", api_dates)
    app.router.add_get("/api/times", api_times)
    app.router.add_post("/api/applications", api_create_application)
    app.router.add_get("/api/admin/slots", api_admin_slots)
    app.router.add_post("/api/admin/slots", api_admin_add_slots)
    app.router.add_delete("/api/admin/slots/{slot_id}", api_admin_delete_slot)
    app.router.add_get("/api/admin/applications", api_admin_applications)
    app.router.add_patch("/api/admin/applications/{application_id}", api_admin_update_application)
    app.router.add_static("/miniapp/static", MINIAPP_DIR, show_index=False)
    app.router.add_static("/", SITE_DIR, show_index=False)
    return app
