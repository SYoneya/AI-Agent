from datetime import datetime

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

from config import ADMIN_IDS
from database.db import (
    NON_STUDENT_WSG,
    RESERVATION_PENDING,
    RESERVATION_WAITING,
    STUDENT_WSG,
    add_reservation,
    get_dormitories,
    get_dormitory_by_id,
    get_reservation_by_id,
    get_user_by_telegram_id,
    is_user_blocked,
)
from keyboards.user import (
    RESERVATION_BUTTONS,
    NON_STUDENT_WSG_TEXTS,
    STUDENT_WSG_TEXTS,
    build_main_menu,
    build_status_menu,
    build_contacts_menu,
)
from locales import all_texts, language_from_user, t
from states.reservation import ReservationForm

router = Router()

ROOM_TYPE_KEYS = ("room_single", "room_double", "room_triple", "room_any")
ALL_ROOM_TYPES = tuple(value for key in ROOM_TYPE_KEYS for value in all_texts(key))

RESERVATION_STATUS_LABELS = {
    RESERVATION_PENDING: "🟡 Очікує розгляду",
    RESERVATION_WAITING: "⏳ У списку очікування",
}

RES_TEXTS = {
    "uk": {
        "choose_dorm": "Оберіть гуртожиток:",
        "dorm_not_found": "Гуртожиток не знайдено.",
        "selected_dorm": "Обрано: {name}",
        "selected_dorm_status": "Обрано: {name}\n\n{status_prompt}",
        "check_in": "Введіть дату заїзду у форматі РРРР-ММ-ДД або ДД.ММ.РРРР:",
        "check_out": "Введіть дату виїзду:",
        "bad_check_in": "Не вдалося розпізнати дату. Приклад: 2026-09-01 або 01.09.2026",
        "bad_check_out": "Не вдалося розпізнати дату. Приклад: 2027-06-30 або 30.06.2027",
        "check_out_after": "Дата виїзду має бути пізніше дати заїзду:",
        "choose_room": "Оберіть тип кімнати:",
        "choose_room_menu": "Оберіть тип кімнати з меню:",
        "restart": "Гуртожиток не знайдено. Почніть бронювання заново.",
        "review": (
            "Перевірте заявку:\n\n"
            "Статус: {status}\n"
            "Гуртожиток: {dormitory}\n"
            "Заїзд: {check_in}\n"
            "Виїзд: {check_out}\n"
            "Тип кімнати: {room_type}\n"
            "Вільні місця зараз: {free_places}\n\n"
            "Підтвердити резервацію?"
        ),
        "waitlisted": (
            "⏳ Заявка #{id} додана до списку очікування.\n"
            "Коли місце звільниться, бот автоматично повідомить вас."
        ),
        "created": (
            "✅ Заявка #{id} створена та передана адміністратору.\n"
            "Статус: 🟡 Очікує розгляду."
        ),
        "cancelled": "Резервацію скасовано.",
    },
    "en": {
        "choose_dorm": "Choose a dormitory:",
        "dorm_not_found": "Dormitory not found.",
        "selected_dorm": "Selected: {name}",
        "selected_dorm_status": "Selected: {name}\n\n{status_prompt}",
        "check_in": "Enter the check-in date in YYYY-MM-DD or DD.MM.YYYY format:",
        "check_out": "Enter the check-out date:",
        "bad_check_in": "Could not recognize the date. Example: 2026-09-01 or 01.09.2026",
        "bad_check_out": "Could not recognize the date. Example: 2027-06-30 or 30.06.2027",
        "check_out_after": "The check-out date must be later than the check-in date:",
        "choose_room": "Choose a room type:",
        "choose_room_menu": "Choose a room type from the menu:",
        "restart": "Dormitory not found. Please start the reservation again.",
        "review": (
            "Check your request:\n\n"
            "Status: {status}\n"
            "Dormitory: {dormitory}\n"
            "Check-in: {check_in}\n"
            "Check-out: {check_out}\n"
            "Room type: {room_type}\n"
            "Free places now: {free_places}\n\n"
            "Confirm the reservation?"
        ),
        "waitlisted": (
            "⏳ Request #{id} was added to the waiting list.\n"
            "When a place becomes available, the bot will notify you automatically."
        ),
        "created": (
            "✅ Request #{id} was created and sent to the administrator.\n"
            "Status: 🟡 Pending review."
        ),
        "cancelled": "Reservation cancelled.",
    },
    "pl": {
        "choose_dorm": "Wybierz akademik:",
        "dorm_not_found": "Nie znaleziono akademika.",
        "selected_dorm": "Wybrano: {name}",
        "selected_dorm_status": "Wybrano: {name}\n\n{status_prompt}",
        "check_in": "Podaj datę zakwaterowania w formacie RRRR-MM-DD lub DD.MM.RRRR:",
        "check_out": "Podaj datę wykwaterowania:",
        "bad_check_in": "Nie udało się rozpoznać daty. Przykład: 2026-09-01 lub 01.09.2026",
        "bad_check_out": "Nie udało się rozpoznać daty. Przykład: 2027-06-30 lub 30.06.2027",
        "check_out_after": "Data wykwaterowania musi być późniejsza niż data zakwaterowania:",
        "choose_room": "Wybierz typ pokoju:",
        "choose_room_menu": "Wybierz typ pokoju z menu:",
        "restart": "Nie znaleziono akademika. Rozpocznij rezerwację ponownie.",
        "review": (
            "Sprawdź zgłoszenie:\n\n"
            "Status: {status}\n"
            "Akademik: {dormitory}\n"
            "Zakwaterowanie: {check_in}\n"
            "Wykwaterowanie: {check_out}\n"
            "Typ pokoju: {room_type}\n"
            "Wolne miejsca teraz: {free_places}\n\n"
            "Potwierdzić rezerwację?"
        ),
        "waitlisted": (
            "⏳ Zgłoszenie #{id} dodano do listy oczekujących.\n"
            "Gdy miejsce się zwolni, bot automatycznie Cię powiadomi."
        ),
        "created": (
            "✅ Zgłoszenie #{id} utworzono i przekazano administratorowi.\n"
            "Status: 🟡 Oczekuje na rozpatrzenie."
        ),
        "cancelled": "Rezerwacja anulowana.",
    },
}


def rt(language: str, key: str, **kwargs) -> str:
    value = RES_TEXTS.get(language, RES_TEXTS["uk"]).get(key, RES_TEXTS["uk"][key])
    return value.format(**kwargs) if kwargs else value


def normalize_wsg_status(text: str) -> str | None:
    if text in STUDENT_WSG_TEXTS:
        return STUDENT_WSG
    if text in NON_STUDENT_WSG_TEXTS:
        return NON_STUDENT_WSG
    return None


def status_title(status: str | None, language: str = "uk") -> str:
    return t(language, "status_student") if status == STUDENT_WSG else t(language, "status_non_student")


def room_type_menu(language: str = "uk") -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t(language, key))] for key in ROOM_TYPE_KEYS],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def dormitories_keyboard(dormitories) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"{dormitory['name']} · вільно {dormitory['free_places']}",
                    callback_data=f"res:dorm:{dormitory['id']}",
                )
            ]
            for dormitory in dormitories
        ]
    )


def confirmation_keyboard(language: str = "uk") -> InlineKeyboardMarkup:
    confirm_text = {"uk": "✅ Підтвердити", "en": "✅ Confirm", "pl": "✅ Potwierdź"}.get(language, "✅ Підтвердити")
    cancel_text = {"uk": "❌ Скасувати", "en": "❌ Cancel", "pl": "❌ Anuluj"}.get(language, "❌ Скасувати")
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=confirm_text,
                    callback_data="reservation:confirm",
                )
            ],
            [
                InlineKeyboardButton(
                    text=cancel_text,
                    callback_data="reservation:cancel",
                )
            ],
        ]
    )


def parse_date(value: str):
    value = value.strip()
    for fmt in ("%Y-%m-%d", "%d.%m.%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


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
            t(language, "feature_blocked"),
            reply_markup=build_contacts_menu(language),
        )
        return False

    return True


async def ensure_registered_callback(callback: CallbackQuery) -> bool:
    user = await get_user_by_telegram_id(callback.from_user.id)
    language = language_from_user(user)
    if not user or user["status"] != "registered":
        await callback.answer(
            t(language, "auth_required"),
            show_alert=True,
        )
        return False

    if await is_user_blocked(callback.from_user.id):
        await callback.answer(
            t(language, "feature_blocked"),
            show_alert=True,
        )
        return False

    return True


async def ask_applicant_status(message: Message, state: FSMContext):
    user = await get_user_by_telegram_id(message.from_user.id)
    language = language_from_user(user)
    await state.set_state(ReservationForm.applicant_status)
    await message.answer(t(language, "choose_status"), reply_markup=build_status_menu(language))


async def ask_check_in(message: Message, state: FSMContext):
    user = await get_user_by_telegram_id(message.from_user.id)
    language = language_from_user(user)
    await state.set_state(ReservationForm.check_in)
    await message.answer(
        rt(language, "check_in"),
        reply_markup=ReplyKeyboardRemove(),
    )


async def notify_admins_about_reservation(bot, reservation_id: int):
    reservation = await get_reservation_by_id(reservation_id)
    if not reservation:
        return

    text = (
        f"📥 Нова резервація #{reservation['id']}\n\n"
        f"Користувач: {reservation['name']} {reservation['surname']}\n"
        f"Статус: {status_title(reservation['applicant_status'] or reservation['wsg_status'])}\n"
        f"Гуртожиток: {reservation['dormitory_name']}\n"
        f"Заїзд: {reservation['check_in']}\n"
        f"Виїзд: {reservation['check_out']}\n"
        f"Тип кімнати: {reservation['room_type']}\n"
        f"Стан заявки: {RESERVATION_STATUS_LABELS.get(reservation['status'], reservation['status'])}"
    )
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Відкрити заявку",
                    callback_data=f"admin:res:{reservation_id}",
                )
            ]
        ]
    )

    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, text, reply_markup=keyboard)
        except Exception:
            pass


@router.message(F.text.in_(RESERVATION_BUTTONS))
async def reservation_start(message: Message, state: FSMContext):
    if not await ensure_registered_message(message):
        return

    await state.clear()
    await ask_applicant_status(message, state)


@router.callback_query(F.data.startswith("book:dorm:"))
async def reservation_from_dormitory(callback: CallbackQuery, state: FSMContext):
    if not await ensure_registered_callback(callback):
        return

    user = await get_user_by_telegram_id(callback.from_user.id)
    language = language_from_user(user)
    dormitory_id = int(callback.data.split(":")[2])
    dormitory = await get_dormitory_by_id(dormitory_id)
    if not dormitory:
        await callback.answer(rt(language, "dorm_not_found"), show_alert=True)
        return

    await state.clear()
    await state.update_data(
        dormitory_id=dormitory["id"],
        dormitory_name=dormitory["name"],
    )
    await callback.message.answer(
        rt(language, "selected_dorm_status", name=dormitory["name"], status_prompt=t(language, "choose_status")),
        reply_markup=build_status_menu(language),
    )
    await state.set_state(ReservationForm.applicant_status)
    await callback.answer()


@router.message(ReservationForm.applicant_status, F.text)
async def reservation_get_status(message: Message, state: FSMContext):
    user = await get_user_by_telegram_id(message.from_user.id)
    language = language_from_user(user)
    applicant_status = normalize_wsg_status(message.text.strip())
    if applicant_status is None:
        await message.answer(t(language, "choose_option"), reply_markup=build_status_menu(language))
        return

    await state.update_data(applicant_status=applicant_status)
    data = await state.get_data()

    if data.get("dormitory_id"):
        await ask_check_in(message, state)
        return

    dormitories = await get_dormitories()
    await state.set_state(ReservationForm.dormitory)
    await message.answer(
        rt(language, "choose_dorm"),
        reply_markup=dormitories_keyboard(dormitories),
    )


@router.callback_query(ReservationForm.dormitory, F.data.startswith("res:dorm:"))
async def reservation_get_dormitory(callback: CallbackQuery, state: FSMContext):
    if not await ensure_registered_callback(callback):
        return

    user = await get_user_by_telegram_id(callback.from_user.id)
    language = language_from_user(user)
    dormitory_id = int(callback.data.split(":")[2])
    dormitory = await get_dormitory_by_id(dormitory_id)
    if not dormitory:
        await callback.answer(rt(language, "dorm_not_found"), show_alert=True)
        return

    await state.update_data(
        dormitory_id=dormitory["id"],
        dormitory_name=dormitory["name"],
    )
    await callback.message.edit_text(rt(language, "selected_dorm", name=dormitory["name"]))
    await callback.message.answer(
        rt(language, "check_in"),
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.set_state(ReservationForm.check_in)
    await callback.answer()


@router.message(ReservationForm.check_in, F.text)
async def reservation_get_check_in(message: Message, state: FSMContext):
    user = await get_user_by_telegram_id(message.from_user.id)
    language = language_from_user(user)
    check_in = parse_date(message.text)
    if not check_in:
        await message.answer(rt(language, "bad_check_in"))
        return

    await state.update_data(check_in=check_in.isoformat())
    await message.answer(rt(language, "check_out"))
    await state.set_state(ReservationForm.check_out)


@router.message(ReservationForm.check_out, F.text)
async def reservation_get_check_out(message: Message, state: FSMContext):
    user = await get_user_by_telegram_id(message.from_user.id)
    language = language_from_user(user)
    check_out = parse_date(message.text)
    if not check_out:
        await message.answer(rt(language, "bad_check_out"))
        return

    data = await state.get_data()
    check_in = datetime.fromisoformat(data["check_in"]).date()
    if check_out <= check_in:
        await message.answer(rt(language, "check_out_after"))
        return

    await state.update_data(check_out=check_out.isoformat())
    await message.answer(rt(language, "choose_room"), reply_markup=room_type_menu(language))
    await state.set_state(ReservationForm.room_type)


@router.message(ReservationForm.room_type, F.text)
async def reservation_get_room_type(message: Message, state: FSMContext):
    user = await get_user_by_telegram_id(message.from_user.id)
    language = language_from_user(user)
    room_type = message.text.strip()
    if room_type not in ALL_ROOM_TYPES:
        await message.answer(rt(language, "choose_room_menu"), reply_markup=room_type_menu(language))
        return

    await state.update_data(room_type=room_type)
    data = await state.get_data()
    dormitory = await get_dormitory_by_id(data["dormitory_id"])
    if not dormitory:
        await message.answer(rt(language, "restart"))
        await state.clear()
        return

    text = rt(
        language,
        "review",
        status=status_title(data["applicant_status"], language),
        dormitory=dormitory["name"],
        check_in=data["check_in"],
        check_out=data["check_out"],
        room_type=room_type,
        free_places=dormitory["free_places"],
    )
    await message.answer(
        text,
        reply_markup=confirmation_keyboard(language),
    )
    await state.set_state(ReservationForm.confirmation)


@router.callback_query(ReservationForm.confirmation, F.data == "reservation:confirm")
async def reservation_confirm(callback: CallbackQuery, state: FSMContext):
    if not await ensure_registered_callback(callback):
        return

    user = await get_user_by_telegram_id(callback.from_user.id)
    language = language_from_user(user)
    data = await state.get_data()
    reservation_id, status = await add_reservation(
        user["id"],
        data["dormitory_id"],
        data["check_in"],
        data["check_out"],
        data["room_type"],
        data["applicant_status"],
    )
    await state.clear()

    if status == RESERVATION_WAITING:
        answer = rt(language, "waitlisted", id=reservation_id)
    else:
        answer = rt(language, "created", id=reservation_id)

    await callback.message.edit_text(answer)
    await callback.message.answer(
        t(language, "main_menu"),
        reply_markup=build_main_menu(language, is_admin=user["telegram_id"] in ADMIN_IDS or user["is_admin"]),
    )
    await notify_admins_about_reservation(callback.bot, reservation_id)
    await callback.answer()


@router.callback_query(ReservationForm.confirmation, F.data == "reservation:cancel")
async def reservation_cancel(callback: CallbackQuery, state: FSMContext):
    user = await get_user_by_telegram_id(callback.from_user.id)
    language = language_from_user(user)
    await state.clear()
    await callback.message.edit_text(rt(language, "cancelled"))
    await callback.message.answer(
        t(language, "main_menu"),
        reply_markup=build_main_menu(language, is_admin=bool(user and (user["telegram_id"] in ADMIN_IDS or user["is_admin"]))),
    )
    await callback.answer()
