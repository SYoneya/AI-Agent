from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from database.db import (
    add_reservation,
    get_dormitories,
    get_room_by_id,
    get_rooms_by_dormitory,
    get_user_by_telegram_id,
    is_user_blocked,
    set_room_reserved,
)

router = Router()

STATUS_LABELS = {
    "available": "свободна",
    "reserved": "занята",
}


async def ensure_registered_callback(callback: CallbackQuery) -> bool:
    user = await get_user_by_telegram_id(callback.from_user.id)
    if not user or user["status"] != "registered":
        await callback.answer(
            "Эта функция доступна только после одобрения регистрации.",
            show_alert=True,
        )
        return False

    if await is_user_blocked(callback.from_user.id):
        await callback.answer(
            "Ваш аккаунт заблокирован. Вы не можете бронировать комнаты.",
            show_alert=True,
        )
        return False

    return True


@router.callback_query(F.data.startswith("dorm:"))
async def show_rooms(callback: CallbackQuery):
    if not await ensure_registered_callback(callback):
        return

    dormitory_name = callback.data.split(":", 1)[1]
    rooms = await get_rooms_by_dormitory(dormitory_name)

    if not rooms:
        await callback.answer(
            "Общежитие не найдено или в нем нет комнат.",
            show_alert=True,
        )
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=(
                        f"{room['room_number']} - {room['price']} PLN "
                        f"— {STATUS_LABELS.get(room['status'], room['status'])}"
                    ),
                    callback_data=f"room:{room['id']}",
                )
            ]
            for room in rooms
        ]
        + [[InlineKeyboardButton(text="⬅️ Назад", callback_data="back:dormitories")]]
    )

    await callback.message.edit_text(
        f"🚪 Комнаты в {dormitory_name}:",
        reply_markup=keyboard,
    )
    await callback.answer()


@router.callback_query(F.data == "back:dormitories")
async def back_to_dorms(callback: CallbackQuery):
    if not await ensure_registered_callback(callback):
        return

    dorms = await get_dormitories()
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=dorm, callback_data=f"dorm:{dorm}")]
            for dorm in dorms
        ]
    )

    await callback.message.edit_text("Выберите общежитие:", reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("room:"))
async def reserve_room(callback: CallbackQuery):
    user = await get_user_by_telegram_id(callback.from_user.id)

    if not user or user["status"] != "registered":
        await callback.answer(
            "Эта функция доступна только после одобрения регистрации.",
            show_alert=True,
        )
        return

    if await is_user_blocked(callback.from_user.id):
        await callback.answer(
            "Ваш аккаунт заблокирован. Вы не можете бронировать комнаты.",
            show_alert=True,
        )
        return

    room_id = int(callback.data.split(":", 1)[1])
    room = await get_room_by_id(room_id)

    if not room:
        await callback.answer("Комната не найдена.", show_alert=True)
        return

    if room["status"] != "available":
        await callback.answer("Эта комната уже занята.", show_alert=True)
        return

    await add_reservation(user["id"], room_id)
    await set_room_reserved(room_id)

    await callback.message.edit_text(
        f"✅ Заявка на комнату {room['room_number']} отправлена администратору."
    )
    await callback.answer()
