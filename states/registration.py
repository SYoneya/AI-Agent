from aiogram.fsm.state import State, StatesGroup


class Registration(StatesGroup):
    name = State()
    surname = State()
    city = State()
    age = State()
    education = State()
    university = State()