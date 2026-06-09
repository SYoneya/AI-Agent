from aiogram.fsm.state import State, StatesGroup


class IssueForm(StatesGroup):
    dormitory = State()
    category = State()
    description = State()
    photo = State()
