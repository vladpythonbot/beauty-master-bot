from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

from database import Database
from keyboards import admin_application_keyboard, admin_menu, main_menu
from texts import format_date, services_text


router = Router()
MINI_APP_URL = ""


def menu(user_id: int | None = None, admin_id: int | None = None):
    return main_menu(MINI_APP_URL, bool(user_id and admin_id and is_admin(user_id, admin_id)))


def register_handlers(db: Database, admin_id: int, mini_app_url: str = "") -> Router:
    global MINI_APP_URL
    MINI_APP_URL = mini_app_url
    router.message.middleware(DbMiddleware(db, admin_id))
    router.callback_query.middleware(DbMiddleware(db, admin_id))
    return router


class DbMiddleware:
    def __init__(self, db: Database, admin_id: int):
        self.db = db
        self.admin_id = admin_id

    async def __call__(self, handler, event, data):
        data["db"] = self.db
        data["admin_id"] = self.admin_id
        return await handler(event, data)


def is_admin(user_id: int, admin_id: int) -> bool:
    return user_id == admin_id


def callback_application_id(callback: CallbackQuery) -> int | None:
    try:
        return int((callback.data or "").split(":", 1)[1])
    except (IndexError, ValueError):
        return None


@router.message(CommandStart())
async def start(message: Message, state: FSMContext, admin_id: int) -> None:
    await state.clear()
    await message.answer(
        "Вітаю! Для перегляду послуг, вільного часу та запису натисніть кнопку під повідомленням.",
        reply_markup=menu(message.from_user.id, admin_id),
    )


@router.message(Command("id"))
async def show_user_id(message: Message) -> None:
    await message.answer(f"Ваш Telegram ID: <code>{message.from_user.id}</code>")


@router.message(Command("services"))
async def show_services(message: Message) -> None:
    await message.answer(services_text())


@router.message(Command("admin"))
async def admin_panel(message: Message, state: FSMContext, admin_id: int) -> None:
    await state.clear()
    if not is_admin(message.from_user.id, admin_id):
        await message.answer(
            "Адмін-панель не показана, бо ваш Telegram ID не збігається з ADMIN_ID на сервері.\n\n"
            f"Ваш Telegram ID: <code>{message.from_user.id}</code>\n"
            "Поставте це число в Railway Variables як ADMIN_ID і зробіть Redeploy.",
            reply_markup=menu(message.from_user.id, admin_id),
        )
        return

    await message.answer(
        "Натисніть кнопку під повідомленням, щоб відкрити адмін-панель.",
        reply_markup=admin_menu(MINI_APP_URL),
    )


@router.callback_query(F.data.startswith("admin_confirm:"))
async def admin_confirm(callback: CallbackQuery, db: Database, admin_id: int) -> None:
    if not is_admin(callback.from_user.id, admin_id):
        await callback.answer("Недостатньо прав.", show_alert=True)
        return

    application_id = callback_application_id(callback)
    if application_id is None:
        await callback.answer("Некоректна дія.", show_alert=True)
        return

    application, changed = await db.update_status(application_id, "confirmed")
    if not application:
        await callback.answer("Заявку не знайдено.", show_alert=True)
        return
    if not changed:
        await callback.answer("Заявку вже оброблено.", show_alert=True)
        return

    await callback.bot.send_message(
        application["user_id"],
        (
            "✅ Ваш запис підтверджено.\n\n"
            f"Дата: {format_date(application['desired_date'])}\n"
            f"Час: {application['desired_time']}\n"
            f"Майстер: {application['schedule_group'] or 'майстер'}"
        ),
    )
    await callback.message.edit_text(callback.message.html_text + "\n\n✅ Статус: підтверджено")
    await callback.answer("Підтверджено")


@router.callback_query(F.data.startswith("admin_cancel:"))
async def admin_cancel(callback: CallbackQuery, db: Database, admin_id: int) -> None:
    if not is_admin(callback.from_user.id, admin_id):
        await callback.answer("Недостатньо прав.", show_alert=True)
        return

    application_id = callback_application_id(callback)
    if application_id is None:
        await callback.answer("Некоректна дія.", show_alert=True)
        return

    application, changed = await db.update_status(application_id, "cancelled")
    if not application:
        await callback.answer("Заявку не знайдено.", show_alert=True)
        return
    if not changed:
        await callback.answer("Заявку вже оброблено.", show_alert=True)
        return

    await callback.bot.send_message(
        application["user_id"],
        "❌ На жаль, заявку скасовано. Обраний час знову доступний для запису.",
    )
    await callback.message.edit_text(callback.message.html_text + "\n\n❌ Статус: скасовано")
    await callback.answer("Скасовано")


@router.message(F.contact)
async def save_phone_contact(message: Message, db: Database, admin_id: int) -> None:
    contact = message.contact
    if contact.user_id and contact.user_id != message.from_user.id:
        await message.answer(
            "Надішліть, будь ласка, саме свій номер.",
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    phone = contact.phone_number
    application = await db.update_latest_application_contact(message.from_user.id, phone)
    if not application:
        await message.answer(
            "Номер отримано, але активну заявку не знайдено.",
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    await message.bot.send_message(
        admin_id,
        (
            f"📞 Клієнт додав номер до заявки #{application['id']}.\n\n"
            f"Клієнт: {application['client_name']}\n"
            f"Телефон: {phone}\n"
            f"Послуга:\n{application['service']}\n\n"
            f"Дата: {format_date(application['desired_date'])}\n"
            f"Час: {application['desired_time']}"
        ),
    )
    await message.answer(
        "Дякуємо, номер додано до заявки.",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message()
async def fallback(message: Message, admin_id: int) -> None:
    await message.answer(
        "Усе керування записом знаходиться в Mini App. Натисніть кнопку під повідомленням.",
        reply_markup=menu(message.from_user.id, admin_id),
    )
