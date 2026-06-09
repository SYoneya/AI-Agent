import re

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from config import ADMIN_IDS
from database.db import NON_STUDENT_WSG, STUDENT_WSG, update_user_registration
from keyboards.user import (
    NON_STUDENT_WSG_TEXT,
    STUDENT_WSG_TEXT,
    build_main_menu,
    build_status_menu,
)
from states.registration import Registration

router = Router()

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def user_is_admin(telegram_id: int) -> bool:
    return telegram_id in ADMIN_IDS


def normalize_wsg_status(text: str) -> str | None:
    if text == STUDENT_WSG_TEXT:
        return STUDENT_WSG
    if text == NON_STUDENT_WSG_TEXT:
        return NON_STUDENT_WSG
    return None


@router.message(Registration.name)
async def get_name(message: Message, state: FSMContext):
    name = (message.text or "").strip()
    if len(name) < 2:
        await message.answer("Введіть ім'я повністю:")
        return

    await state.update_data(name=name)
    await message.answer("Введіть ваше прізвище:")
    await state.set_state(Registration.surname)


@router.message(Registration.surname)
async def get_surname(message: Message, state: FSMContext):
    surname = (message.text or "").strip()
    if len(surname) < 2:
        await message.answer("Введіть прізвище повністю:")
        return

    await state.update_data(surname=surname)
    await message.answer("Введіть номер телефону:")
    await state.set_state(Registration.phone)


@router.message(Registration.phone)
async def get_phone(message: Message, state: FSMContext):
    phone = (message.text or "").strip()
    digits = re.sub(r"\D", "", phone)
    if len(digits) < 9:
        await message.answer("Введіть коректний номер телефону:")
        return

    await state.update_data(phone=phone)
    await message.answer("Введіть email:")
    await state.set_state(Registration.email)


@router.message(Registration.email)
async def get_email(message: Message, state: FSMContext):
    email = (message.text or "").strip()
    if not EMAIL_RE.match(email):
        await message.answer("Введіть коректний email:")
        return

    await state.update_data(email=email)
    await message.answer("Оберіть ваш статус:", reply_markup=build_status_menu())
    await state.set_state(Registration.wsg_status)


@router.message(Registration.wsg_status, F.text)
async def get_wsg_status(message: Message, state: FSMContext):
    wsg_status = normalize_wsg_status(message.text.strip())
    if wsg_status is None:
        await message.answer(
            "Оберіть один із запропонованих варіантів:",
            reply_markup=build_status_menu(),
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
        "✅ Авторизацію завершено.\n"
        "Тепер ви можете бронювати місце, переглядати гуртожитки та створювати заявки.",
        reply_markup=build_main_menu(is_admin=user_is_admin(message.from_user.id)),
    )
