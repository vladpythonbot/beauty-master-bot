from pathlib import Path

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message

from data import CONTACTS, MASTER_INFO, PORTFOLIO_PHOTOS
from database import Database
from keyboards import (
    admin_application_keyboard,
    application_summary_keyboard,
    cancel_keyboard,
    main_menu,
    service_choice_keyboard,
)
from states import BookingForm
from texts import admin_application_text, application_summary, booking_services_text, format_selected_services, services_text


router = Router()


def register_handlers(db: Database, admin_id: int) -> Router:
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


@router.message(CommandStart())
async def start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "Вітаю! Тут можна швидко переглянути роботи, ціни та залишити заявку на запис.",
        reply_markup=main_menu(),
    )


@router.message(F.text == "Інфо")
async def show_info(message: Message) -> None:
    await message.answer(f"{MASTER_INFO}\n\n{CONTACTS}", reply_markup=main_menu())


@router.message(F.text == "Послуги")
async def show_services(message: Message) -> None:
    await message.answer(
        f"{services_text()}\n\nЩоб залишити заявку, натисніть «Записатися».",
        reply_markup=main_menu(),
    )


@router.message(F.text == "Портфоліо")
async def show_portfolio(message: Message) -> None:
    sent_any_photo = False

    for photo_path in PORTFOLIO_PHOTOS:
        path = Path(photo_path)
        if path.exists():
            await message.answer_photo(FSInputFile(path))
            sent_any_photo = True

    if not sent_any_photo:
        await message.answer(
            "🖼 <b>Портфоліо</b>\n\n"
            "Додайте фотографії робіт у папку <code>assets/portfolio</code> "
            "з назвами <code>work_1.jpg</code>, <code>work_2.jpg</code>, <code>work_3.jpg</code>.",
            reply_markup=main_menu(),
        )


@router.message(F.text == "Записатися")
async def booking_start(message: Message, state: FSMContext) -> None:
    await state.set_state(BookingForm.name)
    await message.answer("Як вас звати?", reply_markup=cancel_keyboard())


@router.message(F.text == "Скасувати")
async def cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Заявку скасовано.", reply_markup=main_menu())


@router.message(BookingForm.name)
async def booking_name(message: Message, state: FSMContext) -> None:
    if not message.text or len(message.text.strip()) < 2:
        await message.answer("Будь ласка, введіть ім'я.")
        return

    await state.update_data(name=message.text.strip(), service_ids=[])
    await state.set_state(BookingForm.service)
    await message.answer(
        booking_services_text([]),
        reply_markup=service_choice_keyboard([]),
    )


@router.callback_query(BookingForm.service, F.data.startswith("service_toggle:"))
async def toggle_service(callback: CallbackQuery, state: FSMContext) -> None:
    service_id = callback.data.split(":", 1)[1]
    data = await state.get_data()
    selected_ids = list(data.get("service_ids", []))

    if service_id in selected_ids:
        selected_ids.remove(service_id)
    else:
        selected_ids.append(service_id)

    await state.update_data(service_ids=selected_ids)
    await callback.message.edit_text(
        booking_services_text(selected_ids),
        reply_markup=service_choice_keyboard(selected_ids),
    )
    await callback.answer()


@router.callback_query(BookingForm.service, F.data == "service_done")
async def finish_service_choice(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    selected_ids = list(data.get("service_ids", []))

    if not selected_ids:
        await callback.answer("Оберіть хоча б одну послугу.", show_alert=True)
        return

    await state.update_data(service=format_selected_services(selected_ids).replace("• ", ""))
    await state.set_state(BookingForm.date)
    await callback.message.answer("Бажана дата? Наприклад: 25.08", reply_markup=cancel_keyboard())
    await callback.answer()


@router.message(BookingForm.service)
async def block_manual_service_input(message: Message) -> None:
    await message.answer("Оберіть послуги кнопками під повідомленням.")


@router.message(BookingForm.date)
async def booking_date(message: Message, state: FSMContext) -> None:
    if not message.text or len(message.text.strip()) < 4:
        await message.answer("Напишіть бажану дату.")
        return

    await state.update_data(date=message.text.strip())
    await state.set_state(BookingForm.time)
    await message.answer("Бажаний час? Наприклад: 14:30", reply_markup=cancel_keyboard())


@router.message(BookingForm.time)
async def booking_time(message: Message, state: FSMContext) -> None:
    if not message.text or len(message.text.strip()) < 2:
        await message.answer("Напишіть бажаний час.")
        return

    await state.update_data(time=message.text.strip())
    await state.set_state(BookingForm.contact)
    await message.answer(
        "Залиште телефон або Telegram username.",
        reply_markup=cancel_keyboard(),
    )


@router.message(BookingForm.contact)
async def booking_contact(message: Message, state: FSMContext) -> None:
    if not message.text or len(message.text.strip()) < 4:
        await message.answer("Будь ласка, залиште телефон або Telegram username.")
        return

    await state.update_data(contact=message.text.strip())
    data = await state.get_data()
    await state.set_state(BookingForm.confirmation)
    await message.answer(
        application_summary(data),
        reply_markup=application_summary_keyboard(),
    )


@router.callback_query(F.data == "client_change")
async def client_change(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(BookingForm.name)
    await callback.message.answer(
        "Заповнимо заявку ще раз. Як вас звати?",
        reply_markup=cancel_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "client_cancel")
async def client_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.answer("Заявку скасовано.", reply_markup=main_menu())
    await callback.answer()


@router.callback_query(F.data == "client_confirm")
async def client_confirm(callback: CallbackQuery, state: FSMContext, db: Database, admin_id: int) -> None:
    data = await state.get_data()
    required_fields = {"name", "service_ids", "date", "time", "contact"}
    if not required_fields.issubset(data) or not data["service_ids"]:
        await callback.message.answer("Заявка неповна. Почніть запис ще раз.", reply_markup=main_menu())
        await state.clear()
        await callback.answer()
        return

    user = callback.from_user
    application_id = await db.create_application(
        user_id=user.id,
        username=user.username,
        client_name=data["name"],
        service=format_selected_services(data["service_ids"]).replace("• ", ""),
        desired_date=data["date"],
        desired_time=data["time"],
        contact=data["contact"],
    )

    await callback.bot.send_message(
        admin_id,
        admin_application_text(application_id, user.id, user.username, data),
        reply_markup=admin_application_keyboard(application_id),
    )
    await state.clear()
    await callback.message.answer(
        "Дякуємо! Заявку отримано. Майстер зв'яжеться з вами для підтвердження запису.",
        reply_markup=main_menu(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_confirm:"))
async def admin_confirm(callback: CallbackQuery, db: Database, admin_id: int) -> None:
    if callback.from_user.id != admin_id:
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
    if callback.from_user.id != admin_id:
        await callback.answer("Недостатньо прав.", show_alert=True)
        return

    application_id = int(callback.data.split(":")[1])
    application = await db.update_status(application_id, "cancelled")
    if not application:
        await callback.answer("Заявку не знайдено.", show_alert=True)
        return

    await callback.bot.send_message(
        application["user_id"],
        "❌ На жаль, заявку скасовано. Напишіть майстру або залиште нову заявку на інший час.",
    )
    await callback.message.edit_text(callback.message.html_text + "\n\n❌ Статус: скасовано")
    await callback.answer("Скасовано")


@router.message()
async def fallback(message: Message) -> None:
    await message.answer("Оберіть пункт у меню нижче.", reply_markup=main_menu())
