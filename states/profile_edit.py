from aiogram.fsm.state import State, StatesGroup


class ProfileEdit(StatesGroup):
    waiting = State()
