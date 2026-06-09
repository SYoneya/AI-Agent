from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from database.db import (
    ISSUE_IN_PROGRESS,
    ISSUE_NEW,
    ISSUE_RESOLVED,
    RESERVATION_APPROVED,
    RESERVATION_CANCELLED,
    RESERVATION_PENDING,
    RESERVATION_REJECTED,
    RESERVATION_WAITING,
    cancel_reservation,
    get_issue_by_id,
    get_issues_by_user_id,
    get_reservation_by_id,
    get_reservations_by_user_id,
    get_user_by_telegram_id,
    is_user_blocked,
)
from keyboards.user import MY_REQUESTS_BUTTONS, contacts_menu

router = Router()

RESERVATION_STATUS_LABELS = {
    RESERVATION_PENDING: "🟡 Очікує розгляду",
    RESERVATION_APPROVED: "🟢 Підтверджено",
    RESERVATION_REJECTED: "🔴 Відхилено",
    RESERVATION_WAITING: "⏳ У списку очікування",
    RESERVATION_CANCELLED: "⚪ Скасовано",
}

ISSUE_STATUS_LABELS = {
    ISSUE_NEW: "🟡 Нова",
    ISSUE_IN_PROGRESS: "🔵 В роботі",
    ISSUE_RESOLVED: "🟢 Вирішено",
}


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
            "🚫 Ваш акаунт заблоковано. Перегляд заявок недоступний.",
            reply_markup=contacts_menu,
        )
        return False

    return True


def build_cancel_keyboard(reservations) -> InlineKeyboardMarkup | None:
    buttons = []
    for reservation in reservations:
        if reservation["status"] in {RESERVATION_PENDING, RESERVATION_WAITING}:
            buttons.append(
                [
                    InlineKeyboardButton(
                        text=f"Скасувати резервацію #{reservation['id']}",
                        callback_data=f"cancel_res:{reservation['id']}",
                    )
                ]
            )

    if not buttons:
        return None

    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(F.text.in_(MY_REQUESTS_BUTTONS))
async def my_requests(message: Message):
    if not await ensure_registered_message(message):
        return

    user = await get_user_by_telegram_id(message.from_user.id)
    reservations = await get_reservations_by_user_id(user["id"])
    issues = await get_issues_by_user_id(user["id"])

    if not reservations and not issues:
        await message.answer("У вас ще немає заявок.")
        return

    text = "📋 <b>Мої заявки</b>\n\n"

    text += "<b>Резервації</b>\n"
    if reservations:
        for reservation in reservations:
            text += (
                f"#{reservation['id']} · {reservation['created_at']}\n"
                f"Гуртожиток: {reservation['dormitory_name'] or '-'}\n"
                f"Період: {reservation['check_in'] or '-'} - {reservation['check_out'] or '-'}\n"
                f"Тип кімнати: {reservation['room_type'] or '-'}\n"
                f"Статус: {RESERVATION_STATUS_LABELS.get(reservation['status'], reservation['status'])}\n\n"
            )
    else:
        text += "Немає резервацій.\n\n"

    text += "<b>Проблеми</b>\n"
    if issues:
        for issue in issues:
            text += (
                f"Заявка #{issue['id']} · {issue['created_at']}\n"
                f"Гуртожиток: {issue['dormitory_name'] or '-'}\n"
                f"Проблема: {issue['category']}\n"
                f"Статус: {ISSUE_STATUS_LABELS.get(issue['status'], issue['status'])}\n\n"
            )
    else:
        text += "Немає заявок про проблеми."

    await message.answer(text, reply_markup=build_cancel_keyboard(reservations))


@router.callback_query(F.data.startswith("cancel_res:"))
async def cancel_reservation_callback(callback: CallbackQuery):
    user = await get_user_by_telegram_id(callback.from_user.id)
    if not user or user["status"] != "registered":
        await callback.answer(
            "Ця функція доступна після авторизації.",
            show_alert=True,
        )
        return

    reservation_id = int(callback.data.split(":", 1)[1])
    reservation = await get_reservation_by_id(reservation_id)
    if not reservation:
        await callback.answer("Заявку не знайдено.", show_alert=True)
        return

    if reservation["user_id"] != user["id"]:
        await callback.answer("Це не ваша заявка.", show_alert=True)
        return

    if reservation["status"] not in {RESERVATION_PENDING, RESERVATION_WAITING}:
        await callback.answer(
            "Цю заявку вже оброблено, її не можна скасувати тут.",
            show_alert=True,
        )
        return

    promoted = await cancel_reservation(reservation_id)
    await callback.message.edit_text(f"Резервацію #{reservation_id} скасовано.")
    await callback.answer("Заявку скасовано.")

    if promoted:
        try:
            await callback.bot.send_message(
                promoted["telegram_id"],
                f"✅ У {promoted['dormitory_name']} звільнилося місце.\n"
                f"Ваша заявка #{promoted['id']} переведена зі списку очікування "
                "та очікує розгляду адміністратором.",
            )
        except Exception:
            pass
