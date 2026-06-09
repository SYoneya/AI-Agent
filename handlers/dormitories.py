from aiogram import F, Router
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from database.db import get_dormitories, get_user_by_telegram_id, is_user_blocked
from keyboards.user import DORMITORIES_BUTTONS, build_contacts_menu
from locales import language_from_user, t

router = Router()

DORM_TEXTS = {
    "uk": {
        "blocked": "🚫 Ваш акаунт заблоковано. Перегляд гуртожитків недоступний.",
        "empty": "Список гуртожитків поки порожній.",
        "available": "Доступні гуртожитки:",
        "address": "Адресу не вказано",
        "total": "Всього місць",
        "free": "Вільно",
        "book": "Забронювати",
    },
    "en": {
        "blocked": "🚫 Your account is blocked. Dormitory browsing is unavailable.",
        "empty": "The dormitory list is empty for now.",
        "available": "Available dormitories:",
        "address": "Address not specified",
        "total": "Total places",
        "free": "Free",
        "book": "Reserve",
    },
    "pl": {
        "blocked": "🚫 Twoje konto jest zablokowane. Przeglądanie akademików jest niedostępne.",
        "empty": "Lista akademików jest obecnie pusta.",
        "available": "Dostępne akademiki:",
        "address": "Nie podano adresu",
        "total": "Liczba miejsc",
        "free": "Wolne",
        "book": "Zarezerwuj",
    },
}


def dt(language: str, key: str) -> str:
    return DORM_TEXTS.get(language, DORM_TEXTS["uk"]).get(key, DORM_TEXTS["uk"][key])


async def ensure_registered_message(message: Message) -> bool:
    user = await get_user_by_telegram_id(message.from_user.id)
    language = language_from_user(user)
    if not user or user["status"] != "registered":
        await message.answer(
            t(language, "auth_required"),
            reply_markup=build_contacts_menu(language),
        )
        return False

    if await is_user_blocked(message.from_user.id):
        await message.answer(
            dt(language, "blocked"),
            reply_markup=build_contacts_menu(language),
        )
        return False

    return True


def dormitory_text(dormitory, language: str) -> str:
    return (
        f"🏢 <b>{dormitory['name']}</b>\n\n"
        f"📍 {dormitory['address'] or dt(language, 'address')}\n"
        f"💰 {dormitory['price']} zł/month\n"
        f"🛏 {dt(language, 'total')}: {dormitory['total_places']}\n"
        f"✅ {dt(language, 'free')}: {dormitory['free_places']}"
    )


def book_keyboard(dormitory_id: int, language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=dt(language, "book"),
                    callback_data=f"book:dorm:{dormitory_id}",
                )
            ]
        ]
    )


@router.message(F.text.in_(DORMITORIES_BUTTONS))
async def dormitories(message: Message):
    if not await ensure_registered_message(message):
        return

    user = await get_user_by_telegram_id(message.from_user.id)
    language = language_from_user(user)
    dormitories_list = await get_dormitories()
    if not dormitories_list:
        await message.answer(dt(language, "empty"))
        return

    await message.answer(dt(language, "available"))
    for dormitory in dormitories_list:
        text = dormitory_text(dormitory, language)
        keyboard = book_keyboard(dormitory["id"], language)
        photo = (dormitory["photo_url"] or "").strip()

        if photo:
            try:
                await message.answer_photo(photo=photo, caption=text, reply_markup=keyboard)
                continue
            except Exception:
                pass

        await message.answer(text, reply_markup=keyboard)
