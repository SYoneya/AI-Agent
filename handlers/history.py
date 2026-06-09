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
    get_issues_by_user_id,
    get_reservation_by_id,
    get_reservations_by_user_id,
    get_user_by_telegram_id,
    is_user_blocked,
)
from keyboards.user import MY_REQUESTS_BUTTONS, build_contacts_menu
from locales import language_from_user, t

router = Router()

RESERVATION_STATUS_LABELS = {
    "uk": {
        RESERVATION_PENDING: "🟡 Очікує розгляду",
        RESERVATION_APPROVED: "🟢 Підтверджено",
        RESERVATION_REJECTED: "🔴 Відхилено",
        RESERVATION_WAITING: "⏳ У списку очікування",
        RESERVATION_CANCELLED: "⚪ Скасовано",
    },
    "en": {
        RESERVATION_PENDING: "🟡 Pending review",
        RESERVATION_APPROVED: "🟢 Approved",
        RESERVATION_REJECTED: "🔴 Rejected",
        RESERVATION_WAITING: "⏳ Waiting list",
        RESERVATION_CANCELLED: "⚪ Cancelled",
    },
    "pl": {
        RESERVATION_PENDING: "🟡 Oczekuje na rozpatrzenie",
        RESERVATION_APPROVED: "🟢 Potwierdzone",
        RESERVATION_REJECTED: "🔴 Odrzucone",
        RESERVATION_WAITING: "⏳ Lista oczekujących",
        RESERVATION_CANCELLED: "⚪ Anulowane",
    },
}

ISSUE_STATUS_LABELS = {
    "uk": {
        ISSUE_NEW: "🟡 Нова",
        ISSUE_IN_PROGRESS: "🔵 В роботі",
        ISSUE_RESOLVED: "🟢 Вирішено",
    },
    "en": {
        ISSUE_NEW: "🟡 New",
        ISSUE_IN_PROGRESS: "🔵 In progress",
        ISSUE_RESOLVED: "🟢 Resolved",
    },
    "pl": {
        ISSUE_NEW: "🟡 Nowe",
        ISSUE_IN_PROGRESS: "🔵 W trakcie",
        ISSUE_RESOLVED: "🟢 Rozwiązane",
    },
}

HISTORY_TEXTS = {
    "uk": {
        "blocked": "🚫 Ваш акаунт заблоковано. Перегляд заявок недоступний.",
        "empty": "У вас ще немає заявок.",
        "title": "📋 <b>Мої заявки</b>\n\n",
        "reservations": "<b>Резервації</b>\n",
        "no_reservations": "Немає резервацій.\n\n",
        "issues": "<b>Проблеми</b>\n",
        "no_issues": "Немає заявок про проблеми.",
        "dorm": "Гуртожиток",
        "period": "Період",
        "room_type": "Тип кімнати",
        "status": "Статус",
        "issue": "Проблема",
        "request": "Заявка",
        "cancel": "Скасувати резервацію #{id}",
        "not_found": "Заявку не знайдено.",
        "not_yours": "Це не ваша заявка.",
        "cant_cancel": "Цю заявку вже оброблено, її не можна скасувати тут.",
        "cancelled": "Резервацію #{id} скасовано.",
        "cancelled_alert": "Заявку скасовано.",
    },
    "en": {
        "blocked": "🚫 Your account is blocked. Request viewing is unavailable.",
        "empty": "You do not have any requests yet.",
        "title": "📋 <b>My requests</b>\n\n",
        "reservations": "<b>Reservations</b>\n",
        "no_reservations": "No reservations.\n\n",
        "issues": "<b>Problems</b>\n",
        "no_issues": "No problem reports.",
        "dorm": "Dormitory",
        "period": "Period",
        "room_type": "Room type",
        "status": "Status",
        "issue": "Problem",
        "request": "Request",
        "cancel": "Cancel reservation #{id}",
        "not_found": "Request not found.",
        "not_yours": "This is not your request.",
        "cant_cancel": "This request has already been processed and cannot be cancelled here.",
        "cancelled": "Reservation #{id} cancelled.",
        "cancelled_alert": "Request cancelled.",
    },
    "pl": {
        "blocked": "🚫 Twoje konto jest zablokowane. Przeglądanie zgłoszeń jest niedostępne.",
        "empty": "Nie masz jeszcze żadnych zgłoszeń.",
        "title": "📋 <b>Moje zgłoszenia</b>\n\n",
        "reservations": "<b>Rezerwacje</b>\n",
        "no_reservations": "Brak rezerwacji.\n\n",
        "issues": "<b>Problemy</b>\n",
        "no_issues": "Brak zgłoszeń problemów.",
        "dorm": "Akademik",
        "period": "Okres",
        "room_type": "Typ pokoju",
        "status": "Status",
        "issue": "Problem",
        "request": "Zgłoszenie",
        "cancel": "Anuluj rezerwację #{id}",
        "not_found": "Nie znaleziono zgłoszenia.",
        "not_yours": "To nie jest Twoje zgłoszenie.",
        "cant_cancel": "To zgłoszenie zostało już obsłużone i nie można go tutaj anulować.",
        "cancelled": "Rezerwacja #{id} anulowana.",
        "cancelled_alert": "Zgłoszenie anulowane.",
    },
}


def ht(language: str, key: str, **kwargs) -> str:
    value = HISTORY_TEXTS.get(language, HISTORY_TEXTS["uk"]).get(key, HISTORY_TEXTS["uk"][key])
    return value.format(**kwargs) if kwargs else value


def reservation_status(language: str, status: str) -> str:
    return RESERVATION_STATUS_LABELS.get(language, RESERVATION_STATUS_LABELS["uk"]).get(status, status)


def issue_status(language: str, status: str) -> str:
    return ISSUE_STATUS_LABELS.get(language, ISSUE_STATUS_LABELS["uk"]).get(status, status)


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
            ht(language, "blocked"),
            reply_markup=build_contacts_menu(language),
        )
        return False

    return True


def build_cancel_keyboard(reservations, language: str) -> InlineKeyboardMarkup | None:
    buttons = []
    for reservation in reservations:
        if reservation["status"] in {RESERVATION_PENDING, RESERVATION_WAITING}:
            buttons.append(
                [
                    InlineKeyboardButton(
                        text=ht(language, "cancel", id=reservation["id"]),
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
    language = language_from_user(user)
    reservations = await get_reservations_by_user_id(user["id"])
    issues = await get_issues_by_user_id(user["id"])

    if not reservations and not issues:
        await message.answer(ht(language, "empty"))
        return

    text = ht(language, "title")

    text += ht(language, "reservations")
    if reservations:
        for reservation in reservations:
            text += (
                f"#{reservation['id']} · {reservation['created_at']}\n"
                f"{ht(language, 'dorm')}: {reservation['dormitory_name'] or '-'}\n"
                f"{ht(language, 'period')}: {reservation['check_in'] or '-'} - {reservation['check_out'] or '-'}\n"
                f"{ht(language, 'room_type')}: {reservation['room_type'] or '-'}\n"
                f"{ht(language, 'status')}: {reservation_status(language, reservation['status'])}\n\n"
            )
    else:
        text += ht(language, "no_reservations")

    text += ht(language, "issues")
    if issues:
        for issue in issues:
            text += (
                f"{ht(language, 'request')} #{issue['id']} · {issue['created_at']}\n"
                f"{ht(language, 'dorm')}: {issue['dormitory_name'] or '-'}\n"
                f"{ht(language, 'issue')}: {issue['category']}\n"
                f"{ht(language, 'status')}: {issue_status(language, issue['status'])}\n\n"
            )
    else:
        text += ht(language, "no_issues")

    await message.answer(text, reply_markup=build_cancel_keyboard(reservations, language))


@router.callback_query(F.data.startswith("cancel_res:"))
async def cancel_reservation_callback(callback: CallbackQuery):
    user = await get_user_by_telegram_id(callback.from_user.id)
    language = language_from_user(user)
    if not user or user["status"] != "registered":
        await callback.answer(t(language, "auth_required"), show_alert=True)
        return

    reservation_id = int(callback.data.split(":", 1)[1])
    reservation = await get_reservation_by_id(reservation_id)
    if not reservation:
        await callback.answer(ht(language, "not_found"), show_alert=True)
        return

    if reservation["user_id"] != user["id"]:
        await callback.answer(ht(language, "not_yours"), show_alert=True)
        return

    if reservation["status"] not in {RESERVATION_PENDING, RESERVATION_WAITING}:
        await callback.answer(ht(language, "cant_cancel"), show_alert=True)
        return

    promoted = await cancel_reservation(reservation_id)
    await callback.message.edit_text(ht(language, "cancelled", id=reservation_id))
    await callback.answer(ht(language, "cancelled_alert"))

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
