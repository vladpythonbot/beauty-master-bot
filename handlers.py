from datetime import datetime
from pathlib import Path
import re

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message

from data import CONTACTS, PORTFOLIO_PHOTOS
from database import Database
from keyboards import (
    admin_date_keyboard,
    admin_application_keyboard,
    admin_application_list_keyboard,
    admin_menu_keyboard,
    admin_slots_keyboard,
    admin_time_presets_keyboard,
    application_summary_keyboard,
    available_dates_keyboard,
    available_times_keyboard,
    cancel_keyboard,
    format_date,
    main_menu,
    schedule_group_keyboard,
    service_choice_keyboard,
)
from states import AdminSlotForm, BookingForm
from texts import (
    admin_application_text,
    admin_applications_text,
    admin_slots_text,
    application_summary,
    booking_services_text,
    format_selected_services,
    services_text,
)


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


def is_admin(user_id: int, admin_id: int) -> bool:
    return user_id == admin_id


def normalize_date(text: str) -> str | None:
    value = text.strip()
    current_year = datetime.now().year

    for fmt in ("%d.%m.%Y", "%d.%m", "%Y-%m-%d"):
        try:
            parsed = datetime.strptime(value, fmt)
            if fmt == "%d.%m":
                parsed = parsed.replace(year=current_year)
            return parsed.date().isoformat()
        except ValueError:
            continue

    return None


def parse_times(text: str) -> list[str]:
    found = re.findall(r"\b([01]?\d|2[0-3])[:.](\d{2})\b", text)
    times = sorted({f"{int(hour):02d}:{minute}" for hour, minute in found})
    return times


TIME_PRESETS = {
    "morning": ["09:00", "10:00", "11:00"],
    "day": ["12:00", "13:00", "14:00", "15:00"],
    "evening": ["16:00", "17:00", "18:00"],
    "all": ["09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00", "18:00"],
}


async def finish_admin_slots_creation(message: Message, state: FSMContext, db: Database, times: list[str]) -> None:
    data = await state.get_data()
    created = await db.add_slots(data["admin_group_id"], data["admin_slot_date"], times)
    await state.clear()
    await message.answer(
        f"Готово. Додано вікон: <b>{created}</b>.\n"
        f"Дата: <b>{format_date(data['admin_slot_date'])}</b>\n"
        f"Графік: <b>{data['admin_group_name']}</b>\n"
        f"Час: <b>{', '.join(times)}</b>",
        reply_markup=main_menu(),
    )


@router.message(CommandStart())
async def start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "Вітаю! Тут можна переглянути послуги, роботи та залишити заявку на запис.",
        reply_markup=main_menu(),
    )


@router.message(Command("admin"))
async def admin_panel(message: Message, state: FSMContext, admin_id: int) -> None:
    await state.clear()
    if not is_admin(message.from_user.id, admin_id):
        await message.answer("Ця команда доступна лише майстру.")
        return

    await message.answer(
        "⚙️ <b>Адмін-панель</b>\n\n"
        "Оберіть дію.",
        reply_markup=admin_menu_keyboard(),
    )


@router.message(F.text.in_({"Контакти", "Інфо"}))
async def show_info(message: Message) -> None:
    await message.answer(CONTACTS, reply_markup=main_menu())


@router.message(F.text == "Послуги")
async def show_services(message: Message) -> None:
    await message.answer(
        f"{services_text()}\n\nДля заявки натисніть «Записатися».",
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
    await state.set_state(BookingForm.service)
    await state.update_data(service_ids=[])
    await message.answer(
        booking_services_text([]),
        reply_markup=service_choice_keyboard([]),
    )


@router.message(F.text == "Скасувати")
async def cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Дію скасовано.", reply_markup=main_menu())


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
async def finish_service_choice(callback: CallbackQuery, state: FSMContext, db: Database) -> None:
    data = await state.get_data()
    selected_ids = list(data.get("service_ids", []))

    if not selected_ids:
        await callback.answer("Оберіть хоча б одну послугу.", show_alert=True)
        return

    groups = await db.get_schedule_groups()
    await state.set_state(BookingForm.schedule_group)
    await callback.message.answer(
        "Де записатися?",
        reply_markup=schedule_group_keyboard(groups, "book_group"),
    )
    await callback.answer()


@router.message(BookingForm.service)
async def block_manual_service_input(message: Message) -> None:
    await message.answer("Оберіть послуги кнопками під повідомленням.")


@router.callback_query(BookingForm.schedule_group, F.data.startswith("book_group:"))
async def choose_group(callback: CallbackQuery, state: FSMContext, db: Database) -> None:
    group_id = callback.data.split(":", 1)[1]
    group = await db.get_schedule_group(group_id)
    dates = await db.get_available_dates(group_id)

    if not group:
        await callback.answer("Графік не знайдено.", show_alert=True)
        return

    if not dates:
        await state.clear()
        await callback.message.answer(
            "На жаль, зараз немає вільних вікон для цього варіанту. Спробуйте пізніше або напишіть майстру.",
            reply_markup=main_menu(),
        )
        await callback.answer()
        return

    await state.update_data(group_id=group_id, group_name=group["name"])
    await state.set_state(BookingForm.date)
    await callback.message.answer("Оберіть дату.", reply_markup=available_dates_keyboard(dates))
    await callback.answer()


@router.callback_query(BookingForm.date, F.data.startswith("book_date:"))
async def choose_date(callback: CallbackQuery, state: FSMContext, db: Database) -> None:
    slot_date = callback.data.split(":", 1)[1]
    data = await state.get_data()
    slots = await db.get_available_slots(data["group_id"], slot_date)

    if not slots:
        await callback.answer("На цю дату вільних годин вже немає.", show_alert=True)
        return

    await state.update_data(slot_date=slot_date)
    await state.set_state(BookingForm.time)
    await callback.message.answer("Оберіть час.", reply_markup=available_times_keyboard(slots))
    await callback.answer()


@router.callback_query(BookingForm.time, F.data.startswith("book_slot:"))
async def choose_time(callback: CallbackQuery, state: FSMContext, db: Database) -> None:
    slot_id = int(callback.data.split(":", 1)[1])
    slot = await db.get_slot(slot_id)

    if not slot or slot["status"] != "free":
        await callback.answer("Цей час вже недоступний.", show_alert=True)
        return

    await state.update_data(slot_id=slot_id, slot_time=slot["slot_time"])
    await state.set_state(BookingForm.name)
    await callback.message.answer("Як вас звати?", reply_markup=cancel_keyboard())
    await callback.answer()


@router.message(BookingForm.name)
async def booking_name(message: Message, state: FSMContext) -> None:
    if not message.text or len(message.text.strip()) < 2:
        await message.answer("Будь ласка, введіть ім'я.")
        return

    await state.update_data(name=message.text.strip())
    await state.set_state(BookingForm.contact)
    await message.answer("Залиште телефон або Telegram username.", reply_markup=cancel_keyboard())


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
    await state.set_state(BookingForm.service)
    await state.update_data(service_ids=[])
    await callback.message.answer(
        "Заповнимо заявку ще раз. Оберіть послуги.",
        reply_markup=service_choice_keyboard([]),
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
    required_fields = {"name", "service_ids", "group_name", "slot_date", "slot_time", "slot_id", "contact"}
    if not required_fields.issubset(data) or not data["service_ids"]:
        await callback.message.answer("Заявка неповна. Почніть запис ще раз.", reply_markup=main_menu())
        await state.clear()
        await callback.answer()
        return

    user = callback.from_user
    application_id = await db.create_application_for_slot(
        user_id=user.id,
        username=user.username,
        client_name=data["name"],
        service=format_selected_services(data["service_ids"]).replace("• ", ""),
        contact=data["contact"],
        slot_id=data["slot_id"],
    )

    if not application_id:
        await state.clear()
        await callback.message.answer(
            "Цей час щойно зайняли. Будь ласка, створіть заявку ще раз і оберіть інший час.",
            reply_markup=main_menu(),
        )
        await callback.answer()
        return

    await callback.bot.send_message(
        admin_id,
        admin_application_text(application_id, user.id, user.username, data),
        reply_markup=admin_application_keyboard(application_id),
    )
    await state.clear()
    await callback.message.answer(
        "Дякуємо! Заявку отримано. Обраний час тимчасово заблоковано. Майстер підтвердить запис окремим повідомленням.",
        reply_markup=main_menu(),
    )
    await callback.answer()


@router.callback_query(F.data == "admin_add_slots")
async def admin_add_slots(callback: CallbackQuery, state: FSMContext, db: Database, admin_id: int) -> None:
    if not is_admin(callback.from_user.id, admin_id):
        await callback.answer("Недостатньо прав.", show_alert=True)
        return

    groups = await db.get_schedule_groups()
    await state.set_state(AdminSlotForm.group)
    await callback.message.answer(
        "Оберіть графік, куди додати вільні вікна.",
        reply_markup=schedule_group_keyboard(groups, "admin_group"),
    )
    await callback.answer()


@router.callback_query(AdminSlotForm.group, F.data.startswith("admin_group:"))
async def admin_choose_group(callback: CallbackQuery, state: FSMContext, db: Database, admin_id: int) -> None:
    if not is_admin(callback.from_user.id, admin_id):
        await callback.answer("Недостатньо прав.", show_alert=True)
        return

    group_id = callback.data.split(":", 1)[1]
    group = await db.get_schedule_group(group_id)
    if not group:
        await callback.answer("Графік не знайдено.", show_alert=True)
        return

    await state.update_data(admin_group_id=group_id, admin_group_name=group["name"])
    await state.set_state(AdminSlotForm.date)
    await callback.message.answer(
        "Оберіть дату або введіть її вручну.",
        reply_markup=admin_date_keyboard(),
    )
    await callback.answer()


@router.callback_query(AdminSlotForm.date, F.data.startswith("admin_date:"))
async def admin_choose_quick_date(callback: CallbackQuery, state: FSMContext, admin_id: int) -> None:
    if not is_admin(callback.from_user.id, admin_id):
        await callback.answer("Недостатньо прав.", show_alert=True)
        return

    slot_date = callback.data.split(":", 1)[1]
    await state.update_data(admin_slot_date=slot_date)
    await state.set_state(AdminSlotForm.times)
    await callback.message.answer(
        "Оберіть готовий набір часу або введіть свій.",
        reply_markup=admin_time_presets_keyboard(),
    )
    await callback.answer()


@router.callback_query(AdminSlotForm.date, F.data == "admin_date_manual")
async def admin_choose_manual_date(callback: CallbackQuery, admin_id: int) -> None:
    if not is_admin(callback.from_user.id, admin_id):
        await callback.answer("Недостатньо прав.", show_alert=True)
        return

    await callback.message.answer("Напишіть дату. Наприклад: 25.08 або 25.08.2026")
    await callback.answer()


@router.message(AdminSlotForm.date)
async def admin_slot_date(message: Message, state: FSMContext, admin_id: int) -> None:
    if not is_admin(message.from_user.id, admin_id):
        await message.answer("Недостатньо прав.")
        return

    slot_date = normalize_date(message.text or "")
    if not slot_date:
        await message.answer("Не бачу дату. Напишіть у форматі 25.08 або 25.08.2026.")
        return

    await state.update_data(admin_slot_date=slot_date)
    await state.set_state(AdminSlotForm.times)
    await message.answer(
        "Оберіть готовий набір часу або введіть свій.",
        reply_markup=admin_time_presets_keyboard(),
    )


@router.callback_query(AdminSlotForm.times, F.data.startswith("admin_times:"))
async def admin_choose_time_preset(callback: CallbackQuery, state: FSMContext, db: Database, admin_id: int) -> None:
    if not is_admin(callback.from_user.id, admin_id):
        await callback.answer("Недостатньо прав.", show_alert=True)
        return

    preset = callback.data.split(":", 1)[1]
    times = TIME_PRESETS.get(preset, [])
    if not times:
        await callback.answer("Набір часу не знайдено.", show_alert=True)
        return

    await finish_admin_slots_creation(callback.message, state, db, times)
    await callback.answer()


@router.callback_query(AdminSlotForm.times, F.data == "admin_times_manual")
async def admin_choose_manual_times(callback: CallbackQuery, admin_id: int) -> None:
    if not is_admin(callback.from_user.id, admin_id):
        await callback.answer("Недостатньо прав.", show_alert=True)
        return

    await callback.message.answer("Напишіть час через кому або пробіл. Наприклад: 10:00, 12:30, 15:00")
    await callback.answer()


@router.message(AdminSlotForm.times)
async def admin_slot_times(message: Message, state: FSMContext, db: Database, admin_id: int) -> None:
    if not is_admin(message.from_user.id, admin_id):
        await message.answer("Недостатньо прав.")
        return

    times = parse_times(message.text or "")
    if not times:
        await message.answer("Не бачу часу. Приклад: 10:00, 12:30, 15:00")
        return

    await finish_admin_slots_creation(message, state, db, times)


@router.callback_query(F.data == "admin_list_slots")
async def admin_list_slots(callback: CallbackQuery, db: Database, admin_id: int) -> None:
    if not is_admin(callback.from_user.id, admin_id):
        await callback.answer("Недостатньо прав.", show_alert=True)
        return

    slots = await db.get_upcoming_slots()
    await callback.message.answer(admin_slots_text(slots), reply_markup=admin_slots_keyboard(slots))
    await callback.answer()


@router.callback_query(F.data == "admin_list_applications")
async def admin_list_applications(callback: CallbackQuery, db: Database, admin_id: int) -> None:
    if not is_admin(callback.from_user.id, admin_id):
        await callback.answer("Недостатньо прав.", show_alert=True)
        return

    applications = await db.get_recent_applications()
    await callback.message.answer(
        admin_applications_text(applications),
        reply_markup=admin_application_list_keyboard(applications),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_delete_slot:"))
async def admin_delete_slot(callback: CallbackQuery, db: Database, admin_id: int) -> None:
    if not is_admin(callback.from_user.id, admin_id):
        await callback.answer("Недостатньо прав.", show_alert=True)
        return

    slot_id = int(callback.data.split(":", 1)[1])
    deleted = await db.delete_slot(slot_id)
    if not deleted:
        await callback.answer("Можна видалити лише вільне вікно.", show_alert=True)
        return

    await callback.message.answer("Вікно видалено.")
    await callback.answer()


@router.callback_query(F.data.startswith("admin_edit_slot:"))
async def admin_edit_slot(callback: CallbackQuery, state: FSMContext, db: Database, admin_id: int) -> None:
    if not is_admin(callback.from_user.id, admin_id):
        await callback.answer("Недостатньо прав.", show_alert=True)
        return

    slot_id = int(callback.data.split(":", 1)[1])
    slot = await db.get_slot(slot_id)
    if not slot or slot["status"] != "free":
        await callback.answer("Редагувати можна лише вільне вікно.", show_alert=True)
        return

    await state.update_data(admin_edit_slot_id=slot_id)
    await state.set_state(AdminSlotForm.edit_time)
    await callback.message.answer(
        f"Поточний час: <b>{slot['slot_time']}</b>.\n"
        "Напишіть новий час. Наприклад: 14:30"
    )
    await callback.answer()


@router.message(AdminSlotForm.edit_time)
async def admin_edit_slot_time(message: Message, state: FSMContext, db: Database, admin_id: int) -> None:
    if not is_admin(message.from_user.id, admin_id):
        await message.answer("Недостатньо прав.")
        return

    times = parse_times(message.text or "")
    if len(times) != 1:
        await message.answer("Напишіть один новий час. Наприклад: 14:30")
        return

    data = await state.get_data()
    updated = await db.update_slot_time(data["admin_edit_slot_id"], times[0])
    await state.clear()

    if not updated:
        await message.answer(
            "Не вдалося змінити вікно. Воно вже зайняте або такий час уже існує.",
            reply_markup=main_menu(),
        )
        return

    await message.answer("Вікно оновлено.", reply_markup=main_menu())


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
    await message.answer("Оберіть пункт у меню нижче.", reply_markup=main_menu())
