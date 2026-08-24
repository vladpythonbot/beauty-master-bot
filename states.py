from aiogram.fsm.state import State, StatesGroup


class BookingForm(StatesGroup):
    name = State()
    service = State()
    date = State()
    time = State()
    contact = State()
    confirmation = State()
