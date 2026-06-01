from aiogram import F, Router
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from database.db import get_dormitories, get_user_by_telegram_id, is_user_blocked
from keyboards.user import DORMITORIES_BUTTONS, contacts_menu

router = Router()


@router.message(F.text.in_(DORMITORIES_BUTTONS))
async def dormitories(message: Message):
    user = await get_user_by_telegram_id(message.from_user.id)

    if not user or user["status"] != "registered":
        await message.answer(
            "Эта функция доступна только после одобрения регистрации.",
            reply_markup=contacts_menu,
        )
        return

    if await is_user_blocked(message.from_user.id):
        await message.answer(
            "🚫 Ваш аккаунт заблокирован. Вы не можете просматривать общежития.",
            reply_markup=contacts_menu,
        )
        return

    dorms = await get_dormitories()
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=dorm, callback_data=f"dorm:{dorm}")]
            for dorm in dorms
        ]
    )

    await message.answer("Выберите общежитие:", reply_markup=keyboard)
