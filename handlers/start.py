from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from config import ADMIN_IDS
from database.db import add_user, get_user_by_telegram_id, is_user_blocked
from keyboards.user import build_main_menu, contacts_menu
from states.registration import Registration

router = Router()


def user_is_admin(user) -> bool:
    return bool(user and (user["telegram_id"] in ADMIN_IDS or user["is_admin"]))


@router.message(CommandStart())
async def start_cmd(message: Message, state: FSMContext):
    user = await get_user_by_telegram_id(message.from_user.id)

    if user and await is_user_blocked(message.from_user.id):
        await state.clear()
        await message.answer(
            "🚫 Ваш аккаунт заблокирован. Обратитесь к администратору для разблокировки.",
            reply_markup=contacts_menu,
        )
        return

    if user and user["status"] == "registered":
        await state.clear()
        await message.answer(
            f"Привет, {message.from_user.first_name} 👋\nВы уже зарегистрированы.",
            reply_markup=build_main_menu(is_admin=user_is_admin(user)),
        )
        return

    if user and user["status"] == "pending":
        await state.clear()
        await message.answer(
            "Ваша регистрация ожидает одобрения администратором.",
            reply_markup=contacts_menu,
        )
        return

    if not user:
        await add_user(message.from_user.id, message.from_user.first_name)

    await state.clear()
    await message.answer(
        "👋 Добро пожаловать!\n\nВведите ваше имя:",
        reply_markup=contacts_menu,
    )
    await state.set_state(Registration.name)
