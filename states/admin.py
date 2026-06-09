from aiogram.fsm.state import State, StatesGroup


class AdminManage(StatesGroup):
    add_admin_id = State()
    edit_dormitory = State()
