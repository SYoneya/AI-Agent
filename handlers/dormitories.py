from aiogram import F, Router
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from database.db import get_dormitories, get_user_by_telegram_id, is_user_blocked
from keyboards.user import DORMITORIES_BUTTONS, contacts_menu

router = Router()


async def ensure_registered_message(message: Message) -> bool:
    user = await get_user_by_telegram_id(message.from_user.id)
    if not user or user["status"] != "registered":
        await message.answer(
            "Ця функція доступна після авторизації. Надішліть /start.",
            reply_markup=contacts_menu,
        )
        return False

    if await is_user_blocked(message.from_user.id):
        await message.answer(
            "🚫 Ваш акаунт заблоковано. Перегляд гуртожитків недоступний.",
            reply_markup=contacts_menu,
        )
        return False

    return True


def dormitory_text(dormitory) -> str:
    return (
        f"🏢 <b>{dormitory['name']}</b>\n\n"
        f"📍 {dormitory['address'] or 'Адресу не вказано'}\n"
        f"💰 {dormitory['price']} zł/місяць\n"
        f"🛏 Всього місць: {dormitory['total_places']}\n"
        f"✅ Вільно: {dormitory['free_places']} місць"
    )


def book_keyboard(dormitory_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Забронювати",
                    callback_data=f"book:dorm:{dormitory_id}",
                )
            ]
        ]
    )


@router.message(F.text.in_(DORMITORIES_BUTTONS))
async def dormitories(message: Message):
    if not await ensure_registered_message(message):
        return

    dormitories_list = await get_dormitories()
    if not dormitories_list:
        await message.answer("Список гуртожитків поки порожній.")
        return

    await message.answer("Доступні гуртожитки:")
    for dormitory in dormitories_list:
        text = dormitory_text(dormitory)
        keyboard = book_keyboard(dormitory["id"])
        photo = (dormitory["photo_url"] or "").strip()

        if photo:
            try:
                await message.answer_photo(photo=photo, caption=text, reply_markup=keyboard)
                continue
            except Exception:
                pass

        await message.answer(text, reply_markup=keyboard)
