from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from config import ADMIN_IDS
from database.db import STUDENT_WSG, get_user_by_telegram_id

router = Router()


def status_label(value: str | None) -> str:
    return "Студент WSG" if value == STUDENT_WSG else "Не студент WSG"


def user_is_admin(user) -> bool:
    return bool(user and (user["telegram_id"] in ADMIN_IDS or user["is_admin"]))


@router.message(Command(commands=["profile"]))
async def profile(message: Message):
    user = await get_user_by_telegram_id(message.from_user.id)
    if not user or user["status"] != "registered":
        await message.answer("Профіль доступний після авторизації. Надішліть /start.")
        return

    admin_line = "\nРоль: адміністратор" if user_is_admin(user) else ""
    await message.answer(
        "👤 <b>Профіль</b>\n\n"
        f"ПІБ: {user['name'] or '-'} {user['surname'] or '-'}\n"
        f"Телефон: {user['phone'] or '-'}\n"
        f"Email: {user['email'] or '-'}\n"
        f"Статус: {status_label(user['wsg_status'])}"
        f"{admin_line}"
    )
