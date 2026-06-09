import re

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from config import ADMIN_IDS
from database.db import (
    NON_STUDENT_WSG,
    STUDENT_WSG,
    get_user_by_telegram_id,
    set_user_language,
    update_user_registration,
)
from keyboards.user import (
    NON_STUDENT_WSG_TEXTS,
    STUDENT_WSG_TEXTS,
    build_contacts_menu,
    build_language_menu,
    build_main_menu,
    build_status_menu,
)
from locales import language_code_from_choice, language_from_user, t
from states.registration import Registration

router = Router()

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def user_is_admin(telegram_id: int) -> bool:
    return telegram_id in ADMIN_IDS


def normalize_wsg_status(text: str) -> str | None:
    text = (text or "").strip()
    if text in STUDENT_WSG_TEXTS:
        return STUDENT_WSG
    if text in NON_STUDENT_WSG_TEXTS:
        return NON_STUDENT_WSG
    return None


async def get_current_language(message: Message, state: FSMContext) -> str:
    data = await state.get_data()
    if data.get("language"):
        return data["language"]

    user = await get_user_by_telegram_id(message.from_user.id)
    return language_from_user(user)


@router.message(Registration.language, F.text)
async def get_language(message: Message, state: FSMContext):
    language = language_code_from_choice(message.text)
    if language is None:
        await message.answer(t("uk", "choose_language"), reply_markup=build_language_menu())
        return

    await set_user_language(message.from_user.id, language)
    await state.update_data(language=language)

    user = await get_user_by_telegram_id(message.from_user.id)
    if user and user["status"] == "registered":
        await state.clear()
        await message.answer(
            t(language, "language_saved"),
            reply_markup=build_main_menu(
                language,
                is_admin=bool(user["telegram_id"] in ADMIN_IDS or user["is_admin"]),
            ),
        )
        return

    await message.answer(
        t(language, "welcome"),
        reply_markup=build_contacts_menu(language),
    )
    await state.set_state(Registration.name)


@router.message(Registration.name)
async def get_name(message: Message, state: FSMContext):
    language = await get_current_language(message, state)
    name = (message.text or "").strip()
    if len(name) < 2:
        await message.answer(t(language, "enter_name_full"))
        return

    await state.update_data(name=name)
    await message.answer(t(language, "enter_surname"))
    await state.set_state(Registration.surname)


@router.message(Registration.surname)
async def get_surname(message: Message, state: FSMContext):
    language = await get_current_language(message, state)
    surname = (message.text or "").strip()
    if len(surname) < 2:
        await message.answer(t(language, "enter_surname_full"))
        return

    await state.update_data(surname=surname)
    await message.answer(t(language, "enter_phone"))
    await state.set_state(Registration.phone)


@router.message(Registration.phone)
async def get_phone(message: Message, state: FSMContext):
    language = await get_current_language(message, state)
    phone = (message.text or "").strip()
    digits = re.sub(r"\D", "", phone)
    if len(digits) < 9:
        await message.answer(t(language, "enter_phone_valid"))
        return

    await state.update_data(phone=phone)
    await message.answer(t(language, "enter_email"))
    await state.set_state(Registration.email)


@router.message(Registration.email)
async def get_email(message: Message, state: FSMContext):
    language = await get_current_language(message, state)
    email = (message.text or "").strip()
    if not EMAIL_RE.match(email):
        await message.answer(t(language, "enter_email_valid"))
        return

    await state.update_data(email=email)
    await message.answer(t(language, "choose_status"), reply_markup=build_status_menu(language))
    await state.set_state(Registration.wsg_status)


@router.message(Registration.wsg_status, F.text)
async def get_wsg_status(message: Message, state: FSMContext):
    language = await get_current_language(message, state)
    wsg_status = normalize_wsg_status(message.text)
    if wsg_status is None:
        await message.answer(
            t(language, "choose_option"),
            reply_markup=build_status_menu(language),
        )
        return

    data = await state.get_data()
    await update_user_registration(
        message.from_user.id,
        data["name"],
        data["surname"],
        data["phone"],
        data["email"],
        wsg_status,
    )
    await state.clear()

    await message.answer(
        t(language, "registration_done"),
        reply_markup=build_main_menu(language, is_admin=user_is_admin(message.from_user.id)),
    )
