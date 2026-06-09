from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from config import ADMIN_IDS
from database.db import add_user, get_user_by_telegram_id, is_user_blocked
from keyboards.user import build_contacts_menu, build_language_menu, build_main_menu
from locales import language_from_user, t
from states.registration import Registration

router = Router()


def user_is_admin(user) -> bool:
    return bool(user and (user["telegram_id"] in ADMIN_IDS or user["is_admin"]))


@router.message(CommandStart())
async def start_cmd(message: Message, state: FSMContext):
    user = await get_user_by_telegram_id(message.from_user.id)
    language = language_from_user(user)

    if user and await is_user_blocked(message.from_user.id):
        await state.clear()
        await message.answer(
            t(language, "blocked"),
            reply_markup=build_contacts_menu(language),
        )
        return

    if not user:
        await add_user(message.from_user.id, message.from_user.first_name)
        user = await get_user_by_telegram_id(message.from_user.id)

    if not user["language"]:
        await state.clear()
        await message.answer(t("uk", "choose_language"), reply_markup=build_language_menu())
        await state.set_state(Registration.language)
        return

    if user["status"] == "registered":
        await state.clear()
        await message.answer(
            t(language, "hello_menu", name=user["name"] or message.from_user.first_name),
            reply_markup=build_main_menu(language, is_admin=user_is_admin(user)),
        )
        return

    await state.clear()
    await message.answer(
        t(language, "welcome"),
        reply_markup=build_contacts_menu(language),
    )
    await state.set_state(Registration.name)


@router.message(Command(commands=["language"]))
async def language_cmd(message: Message, state: FSMContext):
    await add_user(message.from_user.id, message.from_user.first_name)
    await state.clear()
    await message.answer(t("uk", "choose_language"), reply_markup=build_language_menu())
    await state.set_state(Registration.language)
