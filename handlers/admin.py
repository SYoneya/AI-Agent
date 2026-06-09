from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from config import ADMIN_IDS
from database.db import (
    ISSUE_IN_PROGRESS,
    ISSUE_NEW,
    ISSUE_RESOLVED,
    NON_STUDENT_WSG,
    RESERVATION_APPROVED,
    RESERVATION_CANCELLED,
    RESERVATION_PENDING,
    RESERVATION_REJECTED,
    RESERVATION_WAITING,
    STUDENT_WSG,
    add_user,
    approve_reservation,
    get_dormitories,
    get_dormitory_by_id,
    get_issue_by_id,
    get_issues,
    get_pending_reservations,
    get_reservation_by_id,
    get_statistics,
    get_user_by_telegram_id,
    get_waiting_reservations,
    reject_reservation,
    set_user_admin,
    update_dormitory_field,
    update_issue_status,
    update_reservation_status,
)
from keyboards.user import ADMIN_PANEL_BUTTONS, build_main_menu
from states.admin import AdminManage

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

DORMITORY_FIELDS = {
    "price": "вартість",
    "total_places": "кількість місць",
    "free_places": "вільні місця",
    "address": "адреса",
    "photo_url": "фото",
}


def is_config_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


async def is_admin(user_id: int) -> bool:
    if is_config_admin(user_id):
        return True

    user = await get_user_by_telegram_id(user_id)
    return bool(user and user["is_admin"])


async def ensure_admin_message(message: Message) -> bool:
    if await is_admin(message.from_user.id):
        return True

    await message.answer("Доступ заборонено. Ви не адміністратор.")
    return False


async def ensure_admin_callback(callback: CallbackQuery) -> bool:
    if await is_admin(callback.from_user.id):
        return True

    await callback.answer("Доступ заборонено.", show_alert=True)
    return False


def admin_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📥 Нові резервації",
                    callback_data="admin:pending_reservations",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⏳ Список очікування",
                    callback_data="admin:waiting_reservations",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⚠️ Проблеми",
                    callback_data="admin:issues",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📊 Статистика",
                    callback_data="admin:stats",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏢 Управління гуртожитками",
                    callback_data="admin:dormitories",
                )
            ],
        ]
    )


def back_to_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:menu")]
        ]
    )


def student_status_label(value: str | None) -> str:
    if value == STUDENT_WSG:
        return "Студент WSG"
    if value == NON_STUDENT_WSG:
        return "Не студент WSG"
    return "-"


def reservation_detail_text(reservation) -> str:
    return (
        f"📥 <b>Резервація #{reservation['id']}</b>\n\n"
        f"Користувач: {reservation['name'] or '-'} {reservation['surname'] or '-'}\n"
        f"Telegram ID: {reservation['telegram_id'] or '-'}\n"
        f"Телефон: {reservation['phone'] or '-'}\n"
        f"Email: {reservation['email'] or '-'}\n"
        f"Статус користувача: {student_status_label(reservation['applicant_status'] or reservation['wsg_status'])}\n"
        f"Гуртожиток: {reservation['dormitory_name'] or '-'}\n"
        f"Заїзд: {reservation['check_in'] or '-'}\n"
        f"Виїзд: {reservation['check_out'] or '-'}\n"
        f"Тип кімнати: {reservation['room_type'] or '-'}\n"
        f"Вільні місця: {reservation['free_places'] if reservation['free_places'] is not None else '-'}\n"
        f"Статус: {RESERVATION_STATUS_LABELS.get(reservation['status'], reservation['status'])}\n"
        f"Дата створення: {reservation['created_at'] or '-'}"
    )


def reservation_actions_keyboard(reservation) -> InlineKeyboardMarkup:
    buttons = []
    if reservation["status"] == RESERVATION_PENDING:
        buttons.extend(
            [
                [
                    InlineKeyboardButton(
                        text="✅ Підтвердити",
                        callback_data=f"admin:res:{reservation['id']}:approve",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ Відхилити",
                        callback_data=f"admin:res:{reservation['id']}:reject",
                    )
                ],
            ]
        )
    elif reservation["status"] == RESERVATION_WAITING:
        buttons.extend(
            [
                [
                    InlineKeyboardButton(
                        text="🟡 Перевести на розгляд",
                        callback_data=f"admin:res:{reservation['id']}:promote",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ Відхилити",
                        callback_data=f"admin:res:{reservation['id']}:reject",
                    )
                ],
            ]
        )

    buttons.append(
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:pending_reservations")]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def notify_user(bot, telegram_id: int | None, text: str, reply_markup=None):
    if not telegram_id:
        return

    try:
        await bot.send_message(telegram_id, text, reply_markup=reply_markup)
    except Exception:
        pass


async def notify_promoted_waiting_user(bot, promoted):
    if not promoted:
        return

    await notify_user(
        bot,
        promoted["telegram_id"],
        f"✅ У {promoted['dormitory_name']} звільнилося місце.\n"
        f"Ваша заявка #{promoted['id']} переведена зі списку очікування "
        "та очікує розгляду адміністратором.",
    )


def parse_telegram_id_value(value: str | None) -> int | None:
    value = (value or "").strip()
    if not value.isdigit():
        return None
    return int(value)


@router.message(Command(commands=["admin"]))
@router.message(F.text.in_(ADMIN_PANEL_BUTTONS))
async def admin_menu(message: Message):
    if not await ensure_admin_message(message):
        return

    await message.answer("🔐 <b>Адмін-панель</b>", reply_markup=admin_menu_keyboard())


@router.message(Command(commands=["add_admin"]))
async def add_admin_cmd(message: Message):
    if not await ensure_admin_message(message):
        return

    parts = (message.text or "").split(maxsplit=1)
    telegram_id = parse_telegram_id_value(parts[1] if len(parts) == 2 else None)
    if telegram_id is None:
        await message.answer("Використайте формат: /add_admin 123456789")
        return

    await add_user(telegram_id)
    await set_user_admin(telegram_id, True)
    user = await get_user_by_telegram_id(telegram_id)
    await message.answer(f"✅ Telegram ID {telegram_id} додано до адміністраторів.")
    await notify_user(
        message.bot,
        telegram_id,
        "✅ Вам відкрито доступ до адмін-панелі.",
        reply_markup=build_main_menu(is_admin=True)
        if user and user["status"] == "registered"
        else None,
    )


@router.callback_query(F.data == "admin:menu")
async def admin_back_to_menu(callback: CallbackQuery, state: FSMContext):
    if not await ensure_admin_callback(callback):
        return

    await state.clear()
    await callback.message.edit_text(
        "🔐 <b>Адмін-панель</b>",
        reply_markup=admin_menu_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "admin:pending_reservations")
async def admin_pending_reservations(callback: CallbackQuery):
    if not await ensure_admin_callback(callback):
        return

    reservations = await get_pending_reservations()
    if not reservations:
        await callback.message.edit_text(
            "Нових резервацій немає.",
            reply_markup=back_to_menu_keyboard(),
        )
        await callback.answer()
        return

    buttons = []
    for reservation in reservations:
        priority = "WSG" if (reservation["applicant_status"] or reservation["wsg_status"]) == STUDENT_WSG else "не WSG"
        buttons.append(
            [
                InlineKeyboardButton(
                    text=(
                        f"#{reservation['id']} · {reservation['name']} {reservation['surname']} "
                        f"· {reservation['dormitory_name']} · {priority}"
                    ),
                    callback_data=f"admin:res:{reservation['id']}",
                )
            ]
        )

    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:menu")])
    await callback.message.edit_text(
        "📥 <b>Нові резервації</b>\n"
        "Студенти WSG показані першими.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )
    await callback.answer()


@router.callback_query(F.data == "admin:waiting_reservations")
async def admin_waiting_reservations(callback: CallbackQuery):
    if not await ensure_admin_callback(callback):
        return

    reservations = await get_waiting_reservations()
    if not reservations:
        await callback.message.edit_text(
            "Список очікування порожній.",
            reply_markup=back_to_menu_keyboard(),
        )
        await callback.answer()
        return

    buttons = []
    for reservation in reservations:
        priority = "WSG" if (reservation["applicant_status"] or reservation["wsg_status"]) == STUDENT_WSG else "не WSG"
        buttons.append(
            [
                InlineKeyboardButton(
                    text=(
                        f"#{reservation['id']} · {reservation['name']} {reservation['surname']} "
                        f"· {reservation['dormitory_name']} · {priority}"
                    ),
                    callback_data=f"admin:res:{reservation['id']}",
                )
            ]
        )

    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:menu")])
    await callback.message.edit_text(
        "⏳ <b>Список очікування</b>\n"
        "Студенти WSG мають пріоритет.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:res:") & F.data.endswith(":approve"))
async def admin_approve_reservation(callback: CallbackQuery):
    if not await ensure_admin_callback(callback):
        return

    reservation_id = int(callback.data.split(":")[2])
    result = await approve_reservation(reservation_id)
    reservation = await get_reservation_by_id(reservation_id)

    if result == "not_found" or not reservation:
        await callback.answer("Заявку не знайдено.", show_alert=True)
        return
    if result == "not_pending":
        await callback.answer("Цю заявку вже оброблено.", show_alert=True)
        return
    if result == "waitlisted":
        await callback.message.edit_text(
            f"⏳ Для заявки #{reservation_id} немає вільних місць. Її перенесено в список очікування.",
            reply_markup=back_to_menu_keyboard(),
        )
        await notify_user(
            callback.bot,
            reservation["telegram_id"],
            f"⏳ Заявку #{reservation_id} перенесено до списку очікування, бо місць наразі немає.",
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        f"✅ Резервацію #{reservation_id} підтверджено.",
        reply_markup=back_to_menu_keyboard(),
    )
    await notify_user(
        callback.bot,
        reservation["telegram_id"],
        f"✅ Ваша резервація #{reservation_id} підтверджена адміністратором.",
    )
    await callback.answer("Заявку підтверджено.")


@router.callback_query(F.data.startswith("admin:res:") & F.data.endswith(":reject"))
async def admin_reject_reservation(callback: CallbackQuery):
    if not await ensure_admin_callback(callback):
        return

    reservation_id = int(callback.data.split(":")[2])
    reservation = await get_reservation_by_id(reservation_id)
    if not reservation:
        await callback.answer("Заявку не знайдено.", show_alert=True)
        return

    promoted = await reject_reservation(reservation_id)
    await callback.message.edit_text(
        f"❌ Резервацію #{reservation_id} відхилено.",
        reply_markup=back_to_menu_keyboard(),
    )
    await notify_user(
        callback.bot,
        reservation["telegram_id"],
        f"❌ Ваша резервація #{reservation_id} відхилена адміністратором.",
    )
    await notify_promoted_waiting_user(callback.bot, promoted)
    await callback.answer("Заявку відхилено.")


@router.callback_query(F.data.startswith("admin:res:") & F.data.endswith(":promote"))
async def admin_promote_waiting_reservation(callback: CallbackQuery):
    if not await ensure_admin_callback(callback):
        return

    reservation_id = int(callback.data.split(":")[2])
    reservation = await get_reservation_by_id(reservation_id)
    if not reservation:
        await callback.answer("Заявку не знайдено.", show_alert=True)
        return

    if reservation["status"] != RESERVATION_WAITING:
        await callback.answer("Ця заявка не в списку очікування.", show_alert=True)
        return

    await update_reservation_status(reservation_id, RESERVATION_PENDING)
    await callback.message.edit_text(
        f"🟡 Резервацію #{reservation_id} переведено на розгляд.",
        reply_markup=back_to_menu_keyboard(),
    )
    await notify_user(
        callback.bot,
        reservation["telegram_id"],
        f"✅ Ваша заявка #{reservation_id} переведена зі списку очікування "
        "та очікує розгляду адміністратором.",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:res:"))
async def admin_reservation_detail(callback: CallbackQuery):
    if not await ensure_admin_callback(callback):
        return

    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.answer("Невірний формат кнопки.", show_alert=True)
        return

    reservation_id = int(parts[2])
    reservation = await get_reservation_by_id(reservation_id)
    if not reservation:
        await callback.answer("Заявку не знайдено.", show_alert=True)
        return

    await callback.message.edit_text(
        reservation_detail_text(reservation),
        reply_markup=reservation_actions_keyboard(reservation),
    )
    await callback.answer()


@router.callback_query(F.data == "admin:issues")
async def admin_issues(callback: CallbackQuery):
    if not await ensure_admin_callback(callback):
        return

    issues = await get_issues(statuses=[ISSUE_NEW, ISSUE_IN_PROGRESS])
    if not issues:
        await callback.message.edit_text(
            "Активних проблем немає.",
            reply_markup=back_to_menu_keyboard(),
        )
        await callback.answer()
        return

    buttons = []
    for issue in issues:
        buttons.append(
            [
                InlineKeyboardButton(
                    text=(
                        f"#{issue['id']} · {issue['dormitory_name']} · "
                        f"{ISSUE_STATUS_LABELS.get(issue['status'], issue['status'])}"
                    ),
                    callback_data=f"admin:issue:{issue['id']}",
                )
            ]
        )

    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:menu")])
    await callback.message.edit_text(
        "⚠️ <b>Проблеми</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )
    await callback.answer()


def issue_actions_keyboard(issue_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🟡 Нова",
                    callback_data=f"admin:issue:{issue_id}:new",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔵 В роботі",
                    callback_data=f"admin:issue:{issue_id}:in_progress",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🟢 Вирішено",
                    callback_data=f"admin:issue:{issue_id}:resolved",
                )
            ],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:issues")],
        ]
    )


@router.callback_query(F.data.startswith("admin:issue:") & F.data.endswith(":new"))
@router.callback_query(F.data.startswith("admin:issue:") & F.data.endswith(":in_progress"))
@router.callback_query(F.data.startswith("admin:issue:") & F.data.endswith(":resolved"))
async def admin_update_issue_status(callback: CallbackQuery):
    if not await ensure_admin_callback(callback):
        return

    parts = callback.data.split(":")
    issue_id = int(parts[2])
    status = parts[3]
    if status not in {ISSUE_NEW, ISSUE_IN_PROGRESS, ISSUE_RESOLVED}:
        await callback.answer("Невідомий статус.", show_alert=True)
        return

    issue = await get_issue_by_id(issue_id)
    if not issue:
        await callback.answer("Заявку не знайдено.", show_alert=True)
        return

    await update_issue_status(issue_id, status)
    await callback.message.edit_text(
        f"Статус заявки #{issue_id} оновлено: {ISSUE_STATUS_LABELS[status]}",
        reply_markup=back_to_menu_keyboard(),
    )
    await notify_user(
        callback.bot,
        issue["telegram_id"],
        f"Статус вашої заявки #{issue_id} оновлено: {ISSUE_STATUS_LABELS[status]}",
    )
    await callback.answer("Статус оновлено.")


@router.callback_query(F.data.startswith("admin:issue:"))
async def admin_issue_detail(callback: CallbackQuery):
    if not await ensure_admin_callback(callback):
        return

    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.answer("Невірний формат кнопки.", show_alert=True)
        return

    issue_id = int(parts[2])
    issue = await get_issue_by_id(issue_id)
    if not issue:
        await callback.answer("Заявку не знайдено.", show_alert=True)
        return

    text = (
        f"⚠️ <b>Проблема #{issue['id']}</b>\n\n"
        f"Користувач: {issue['name'] or '-'} {issue['surname'] or '-'}\n"
        f"Телефон: {issue['phone'] or '-'}\n"
        f"Email: {issue['email'] or '-'}\n"
        f"Гуртожиток: {issue['dormitory_name'] or '-'}\n"
        f"Категорія: {issue['category'] or '-'}\n"
        f"Опис: {issue['description'] or '-'}\n"
        f"Статус: {ISSUE_STATUS_LABELS.get(issue['status'], issue['status'])}\n"
        f"Дата: {issue['created_at'] or '-'}"
    )

    if issue["photo_file_id"]:
        try:
            await callback.message.answer_photo(
                photo=issue["photo_file_id"],
                caption=text,
                reply_markup=issue_actions_keyboard(issue_id),
            )
            await callback.answer()
            return
        except Exception:
            pass

    await callback.message.edit_text(
        text,
        reply_markup=issue_actions_keyboard(issue_id),
    )
    await callback.answer()


@router.callback_query(F.data == "admin:stats")
async def admin_stats(callback: CallbackQuery):
    if not await ensure_admin_callback(callback):
        return

    stats = await get_statistics()
    text = (
        "📊 <b>Статистика</b>\n\n"
        f"Кількість мешканців: {stats['residents_count']}\n"
        f"Кількість вільних місць: {stats['free_places']}\n"
        f"Нових резервацій: {stats['pending_reservations_count']}\n"
        f"У списку очікування: {stats['waiting_reservations_count']}\n"
        f"Кількість скарг: {stats['issues_count']}\n"
        f"Активних проблем: {stats['active_issues_count']}"
    )
    await callback.message.edit_text(text, reply_markup=back_to_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data == "admin:dormitories")
async def admin_dormitories(callback: CallbackQuery):
    if not await ensure_admin_callback(callback):
        return

    dormitories = await get_dormitories()
    buttons = [
        [
            InlineKeyboardButton(
                text=(
                    f"{dormitory['name']} · {dormitory['free_places']}/"
                    f"{dormitory['total_places']} · {dormitory['price']} zł"
                ),
                callback_data=f"admin:dorm:{dormitory['id']}",
            )
        ]
        for dormitory in dormitories
    ]
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:menu")])

    await callback.message.edit_text(
        "🏢 <b>Управління гуртожитками</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )
    await callback.answer()


def dormitory_detail_text(dormitory) -> str:
    return (
        f"🏢 <b>{dormitory['name']}</b>\n\n"
        f"Адреса: {dormitory['address'] or '-'}\n"
        f"Ціна: {dormitory['price']} zł/місяць\n"
        f"Усього місць: {dormitory['total_places']}\n"
        f"Вільні місця: {dormitory['free_places']}\n"
        f"Фото: {'додано' if dormitory['photo_url'] else 'не додано'}"
    )


def dormitory_edit_keyboard(dormitory_id: int) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text=f"Редагувати {label}",
                callback_data=f"admin:edit_dorm:{dormitory_id}:{field}",
            )
        ]
        for field, label in DORMITORY_FIELDS.items()
    ]
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:dormitories")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.callback_query(F.data.startswith("admin:dorm:"))
async def admin_dormitory_detail(callback: CallbackQuery):
    if not await ensure_admin_callback(callback):
        return

    dormitory_id = int(callback.data.split(":")[2])
    dormitory = await get_dormitory_by_id(dormitory_id)
    if not dormitory:
        await callback.answer("Гуртожиток не знайдено.", show_alert=True)
        return

    await callback.message.edit_text(
        dormitory_detail_text(dormitory),
        reply_markup=dormitory_edit_keyboard(dormitory_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:edit_dorm:"))
async def admin_edit_dormitory_prompt(callback: CallbackQuery, state: FSMContext):
    if not await ensure_admin_callback(callback):
        return

    parts = callback.data.split(":")
    dormitory_id = int(parts[2])
    field = parts[3]
    if field not in DORMITORY_FIELDS:
        await callback.answer("Невідоме поле.", show_alert=True)
        return

    await state.update_data(dormitory_id=dormitory_id, field=field)
    await state.set_state(AdminManage.edit_dormitory)
    prompt = f"Введіть нове значення для поля «{DORMITORY_FIELDS[field]}»:"
    if field == "photo_url":
        prompt = "Надішліть фото або URL. Щоб прибрати фото, введіть: -"

    await callback.message.edit_text(prompt)
    await callback.answer()


@router.message(AdminManage.edit_dormitory)
async def admin_save_dormitory_field(message: Message, state: FSMContext):
    if not await ensure_admin_message(message):
        await state.clear()
        return

    data = await state.get_data()
    dormitory_id = data["dormitory_id"]
    field = data["field"]

    if field in {"price", "total_places", "free_places"}:
        try:
            value = int((message.text or "").strip())
        except ValueError:
            await message.answer("Введіть число:")
            return
        if value < 0:
            await message.answer("Значення не може бути від'ємним:")
            return
    elif field == "photo_url":
        if message.photo:
            value = message.photo[-1].file_id
        else:
            value = (message.text or "").strip()
            if value == "-":
                value = ""
    else:
        value = (message.text or "").strip()
        if not value:
            await message.answer("Значення не може бути порожнім:")
            return

    await update_dormitory_field(dormitory_id, field, value)
    await state.clear()

    dormitory = await get_dormitory_by_id(dormitory_id)
    await message.answer(
        "✅ Дані гуртожитку оновлено.\n\n" + dormitory_detail_text(dormitory),
        reply_markup=dormitory_edit_keyboard(dormitory_id),
    )
