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
            "🚫 Ваш акаунт заблоковано. Зверніться до адміністрації.",
            reply_markup=contacts_menu,
        )
        return

    if user and user["status"] == "registered":
        await state.clear()
        await message.answer(
            f"Вітаю, {user['name'] or message.from_user.first_name}! 👋\n"
            "Оберіть дію в головному меню.",
            reply_markup=build_main_menu(is_admin=user_is_admin(user)),
        )
        return

    if not user:
        await add_user(message.from_user.id, message.from_user.first_name)

    await state.clear()
    await message.answer(
        "👋 Вітаємо в боті гуртожитків WSG!\n\n"
        "Для першого запуску потрібно пройти коротку авторизацію.\n"
        "Введіть ваше ім'я:",
        reply_markup=contacts_menu,
    )
    await state.set_state(Registration.name)
