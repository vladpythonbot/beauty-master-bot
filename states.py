from aiogram.fsm.state import State, StatesGroup


class BookingForm(StatesGroup):
    service = State()
    schedule_group = State()
    date = State()
    time = State()
    name = State()
    contact = State()
    confirmation = State()


class AdminSlotForm(StatesGroup):
    group = State()
    date = State()
    times = State()
    edit_time = State()
