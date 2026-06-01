from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from database.db import (
    get_reservation_by_id,
    get_reservations_by_user_id,
    get_user_by_telegram_id,
    is_user_blocked,
    set_room_available,
    update_reservation_status,
)
from keyboards.user import MY_REQUESTS_BUTTONS, contacts_menu

router = Router()

STATUS_LABELS = {
    "pending": "ожидает",
    "approved": "одобрена",
    "rejected": "отклонена",
    "cancelled": "отменена",
}


@router.message(F.text.in_(MY_REQUESTS_BUTTONS))
async def my_reservations(message: Message):
    user = await get_user_by_telegram_id(message.from_user.id)

    if not user or user["status"] != "registered":
        await message.answer(
            "Эта функция доступна только после одобрения регистрации.",
            reply_markup=contacts_menu,
        )
        return

    if await is_user_blocked(message.from_user.id):
        await message.answer(
            "🚫 Ваш аккаунт заблокирован. Вы не можете просматривать заявки.",
            reply_markup=contacts_menu,
        )
        return

    reservations = await get_reservations_by_user_id(user["id"])
    if not reservations:
        await message.answer("У вас еще нет заявок.")
        return

    text = "📄 Мои заявки:\n\n"
    keyboard_buttons = []
    for reservation in reservations:
        status = STATUS_LABELS.get(reservation["status"], reservation["status"])
        text += (
            f"#{reservation['id']} — {reservation['created_at']}\n"
            f"{reservation['dormitory_name']} {reservation['room_number']} "
            f"— {reservation['price']} PLN\n"
            f"Статус: {status}\n\n"
        )
        if reservation["status"] == "pending":
            keyboard_buttons.append(
                [
                    InlineKeyboardButton(
                        text=f"Отменить #{reservation['id']}",
                        callback_data=f"cancel_res:{reservation['id']}",
                    )
                ]
            )

    reply_markup = (
        InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        if keyboard_buttons
        else None
    )

    await message.answer(text, reply_markup=reply_markup)


@router.callback_query(F.data.startswith("cancel_res:"))
async def cancel_reservation(callback: CallbackQuery):
    user = await get_user_by_telegram_id(callback.from_user.id)
    if not user or user["status"] != "registered":
        await callback.answer(
            "Эта функция доступна только после одобрения регистрации.",
            show_alert=True,
        )
        return

    res_id = int(callback.data.split(":", 1)[1])
    reservation = await get_reservation_by_id(res_id)
    if not reservation:
        await callback.answer("Заявка не найдена.", show_alert=True)
        return

    if reservation["user_id"] != user["id"]:
        await callback.answer("Это не ваша заявка.", show_alert=True)
        return

    if reservation["status"] != "pending":
        await callback.answer(
            "Нельзя отменить заявку: она уже обработана.",
            show_alert=True,
        )
        return

    await update_reservation_status(res_id, "cancelled")
    await set_room_available(reservation["room_id"])

    await callback.message.edit_text(f"Заявка #{res_id} отменена.")
    await callback.answer("Заявка отменена.")
