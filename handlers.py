from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database import Database
from keyboards import admin_application_keyboard, main_menu


router = Router()
MINI_APP_URL = ""


def menu():
    return main_menu(MINI_APP_URL)


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


@router.message(CommandStart())
async def start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "Вітаю! Для перегляду послуг, вільного часу та запису відкрийте Mini App.",
        reply_markup=menu(),
    )


@router.message(Command("admin"))
async def admin_panel(message: Message, state: FSMContext, admin_id: int) -> None:
    await state.clear()
    if not is_admin(message.from_user.id, admin_id):
        await message.answer("Ця команда доступна лише майстру.", reply_markup=menu())
        return

    await message.answer(
        "Адмін-панель тепер у Mini App. Там можна додавати вільні вікна, дивитися заявки й керувати записами.",
        reply_markup=menu(),
    )


@router.callback_query(F.data.startswith("admin_confirm:"))
async def admin_confirm(callback: CallbackQuery, db: Database, admin_id: int) -> None:
    if not is_admin(callback.from_user.id, admin_id):
        await callback.answer("Недостатньо прав.", show_alert=True)
        return

    application_id = int(callback.data.split(":")[1])
    application = await db.update_status(application_id, "confirmed")
    if not application:
        await callback.answer("Заявку не знайдено.", show_alert=True)
        return

    await callback.bot.send_message(
        application["user_id"],
        "✅ Ваш запис підтверджено. Майстер очікує вас у зазначений час.",
    )
    await callback.message.edit_text(callback.message.html_text + "\n\n✅ Статус: підтверджено")
    await callback.answer("Підтверджено")


@router.callback_query(F.data.startswith("admin_cancel:"))
async def admin_cancel(callback: CallbackQuery, db: Database, admin_id: int) -> None:
    if not is_admin(callback.from_user.id, admin_id):
        await callback.answer("Недостатньо прав.", show_alert=True)
        return

    application_id = int(callback.data.split(":")[1])
    application = await db.update_status(application_id, "cancelled")
    if not application:
        await callback.answer("Заявку не знайдено.", show_alert=True)
        return

    await callback.bot.send_message(
        application["user_id"],
        "❌ На жаль, заявку скасовано. Обраний час знову доступний для запису.",
    )
    await callback.message.edit_text(callback.message.html_text + "\n\n❌ Статус: скасовано")
    await callback.answer("Скасовано")


@router.message()
async def fallback(message: Message) -> None:
    await message.answer("Усе керування записом знаходиться в Mini App.", reply_markup=menu())
