from aiogram.fsm.state import State, StatesGroup


class Registration(StatesGroup):
    language = State()
    name = State()
    surname = State()
    phone = State()
    email = State()
    wsg_status = State()
