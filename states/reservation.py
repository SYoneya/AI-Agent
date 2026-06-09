from aiogram.fsm.state import State, StatesGroup


class ReservationForm(StatesGroup):
    applicant_status = State()
    dormitory = State()
    check_in = State()
    check_out = State()
    room_type = State()
    confirmation = State()
