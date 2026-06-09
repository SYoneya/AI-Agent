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
    NON_STUDENT_WSG_TEXT,
    RESERVATION_BUTTONS,
    STUDENT_WSG_TEXT,
    build_main_menu,
    build_status_menu,
    contacts_menu,
)
from states.reservation import ReservationForm

router = Router()

ROOM_TYPES = ("Одномісна", "Двомісна", "Тримісна", "Будь-яка")

RESERVATION_STATUS_LABELS = {
    RESERVATION_PENDING: "🟡 Очікує розгляду",
    RESERVATION_WAITING: "⏳ У списку очікування",
}


def normalize_wsg_status(text: str) -> str | None:
    if text == STUDENT_WSG_TEXT:
        return STUDENT_WSG
    if text == NON_STUDENT_WSG_TEXT:
        return NON_STUDENT_WSG
    return None


def status_title(status: str | None) -> str:
    return "Студент WSG" if status == STUDENT_WSG else "Не студент WSG"


def room_type_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=value)] for value in ROOM_TYPES],
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


def confirmation_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Підтвердити",
                    callback_data="reservation:confirm",
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Скасувати",
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
    if not user or user["status"] != "registered":
        await message.answer(
            "Ця функція доступна після авторизації. Надішліть /start.",
            reply_markup=contacts_menu,
        )
        return False

    if await is_user_blocked(message.from_user.id):
        await message.answer(
            "🚫 Ваш акаунт заблоковано. Бронювання недоступне.",
            reply_markup=contacts_menu,
        )
        return False

    return True


async def ensure_registered_callback(callback: CallbackQuery) -> bool:
    user = await get_user_by_telegram_id(callback.from_user.id)
    if not user or user["status"] != "registered":
        await callback.answer(
            "Ця функція доступна після авторизації. Надішліть /start.",
            show_alert=True,
        )
        return False

    if await is_user_blocked(callback.from_user.id):
        await callback.answer(
            "Ваш акаунт заблоковано. Бронювання недоступне.",
            show_alert=True,
        )
        return False

    return True


async def ask_applicant_status(message: Message, state: FSMContext):
    await state.set_state(ReservationForm.applicant_status)
    await message.answer("Ви є:", reply_markup=build_status_menu())


async def ask_check_in(message: Message, state: FSMContext):
    await state.set_state(ReservationForm.check_in)
    await message.answer(
        "Введіть дату заїзду у форматі РРРР-ММ-ДД або ДД.ММ.РРРР:",
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

    dormitory_id = int(callback.data.split(":")[2])
    dormitory = await get_dormitory_by_id(dormitory_id)
    if not dormitory:
        await callback.answer("Гуртожиток не знайдено.", show_alert=True)
        return

    await state.clear()
    await state.update_data(
        dormitory_id=dormitory["id"],
        dormitory_name=dormitory["name"],
    )
    await callback.message.answer(
        f"Обрано: {dormitory['name']}\n\nВи є:",
        reply_markup=build_status_menu(),
    )
    await state.set_state(ReservationForm.applicant_status)
    await callback.answer()


@router.message(ReservationForm.applicant_status, F.text)
async def reservation_get_status(message: Message, state: FSMContext):
    applicant_status = normalize_wsg_status(message.text.strip())
    if applicant_status is None:
        await message.answer("Оберіть один із запропонованих варіантів:", reply_markup=build_status_menu())
        return

    await state.update_data(applicant_status=applicant_status)
    data = await state.get_data()

    if data.get("dormitory_id"):
        await ask_check_in(message, state)
        return

    dormitories = await get_dormitories()
    await state.set_state(ReservationForm.dormitory)
    await message.answer(
        "Оберіть гуртожиток:",
        reply_markup=dormitories_keyboard(dormitories),
    )


@router.callback_query(ReservationForm.dormitory, F.data.startswith("res:dorm:"))
async def reservation_get_dormitory(callback: CallbackQuery, state: FSMContext):
    if not await ensure_registered_callback(callback):
        return

    dormitory_id = int(callback.data.split(":")[2])
    dormitory = await get_dormitory_by_id(dormitory_id)
    if not dormitory:
        await callback.answer("Гуртожиток не знайдено.", show_alert=True)
        return

    await state.update_data(
        dormitory_id=dormitory["id"],
        dormitory_name=dormitory["name"],
    )
    await callback.message.edit_text(f"Обрано: {dormitory['name']}")
    await callback.message.answer(
        "Введіть дату заїзду у форматі РРРР-ММ-ДД або ДД.ММ.РРРР:",
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.set_state(ReservationForm.check_in)
    await callback.answer()


@router.message(ReservationForm.check_in, F.text)
async def reservation_get_check_in(message: Message, state: FSMContext):
    check_in = parse_date(message.text)
    if not check_in:
        await message.answer("Не вдалося розпізнати дату. Приклад: 2026-09-01 або 01.09.2026")
        return

    await state.update_data(check_in=check_in.isoformat())
    await message.answer("Введіть дату виїзду:")
    await state.set_state(ReservationForm.check_out)


@router.message(ReservationForm.check_out, F.text)
async def reservation_get_check_out(message: Message, state: FSMContext):
    check_out = parse_date(message.text)
    if not check_out:
        await message.answer("Не вдалося розпізнати дату. Приклад: 2027-06-30 або 30.06.2027")
        return

    data = await state.get_data()
    check_in = datetime.fromisoformat(data["check_in"]).date()
    if check_out <= check_in:
        await message.answer("Дата виїзду має бути пізніше дати заїзду:")
        return

    await state.update_data(check_out=check_out.isoformat())
    await message.answer("Оберіть тип кімнати:", reply_markup=room_type_menu())
    await state.set_state(ReservationForm.room_type)


@router.message(ReservationForm.room_type, F.text)
async def reservation_get_room_type(message: Message, state: FSMContext):
    room_type = message.text.strip()
    if room_type not in ROOM_TYPES:
        await message.answer("Оберіть тип кімнати з меню:", reply_markup=room_type_menu())
        return

    await state.update_data(room_type=room_type)
    data = await state.get_data()
    dormitory = await get_dormitory_by_id(data["dormitory_id"])
    if not dormitory:
        await message.answer("Гуртожиток не знайдено. Почніть бронювання заново.")
        await state.clear()
        return

    text = (
        "Перевірте заявку:\n\n"
        f"Статус: {status_title(data['applicant_status'])}\n"
        f"Гуртожиток: {dormitory['name']}\n"
        f"Заїзд: {data['check_in']}\n"
        f"Виїзд: {data['check_out']}\n"
        f"Тип кімнати: {room_type}\n"
        f"Вільні місця зараз: {dormitory['free_places']}\n\n"
        "Підтвердити резервацію?"
    )
    await message.answer(
        text,
        reply_markup=confirmation_keyboard(),
    )
    await state.set_state(ReservationForm.confirmation)


@router.callback_query(ReservationForm.confirmation, F.data == "reservation:confirm")
async def reservation_confirm(callback: CallbackQuery, state: FSMContext):
    if not await ensure_registered_callback(callback):
        return

    user = await get_user_by_telegram_id(callback.from_user.id)
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
        answer = (
            f"⏳ Заявка #{reservation_id} додана до списку очікування.\n"
            "Коли місце звільниться, бот автоматично повідомить вас."
        )
    else:
        answer = (
            f"✅ Заявка #{reservation_id} створена та передана адміністратору.\n"
            "Статус: 🟡 Очікує розгляду."
        )

    await callback.message.edit_text(answer)
    await callback.message.answer(
        "Головне меню:",
        reply_markup=build_main_menu(is_admin=user["telegram_id"] in ADMIN_IDS or user["is_admin"]),
    )
    await notify_admins_about_reservation(callback.bot, reservation_id)
    await callback.answer()


@router.callback_query(ReservationForm.confirmation, F.data == "reservation:cancel")
async def reservation_cancel(callback: CallbackQuery, state: FSMContext):
    user = await get_user_by_telegram_id(callback.from_user.id)
    await state.clear()
    await callback.message.edit_text("Резервацію скасовано.")
    await callback.message.answer(
        "Головне меню:",
        reply_markup=build_main_menu(is_admin=bool(user and (user["telegram_id"] in ADMIN_IDS or user["is_admin"]))),
    )
    await callback.answer()
