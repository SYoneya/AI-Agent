from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from config import ADMIN_IDS
from database.db import (
    add_user,
    get_all_users,
    get_pending_reservations,
    get_registered_users,
    get_reservation_by_id,
    get_reservations_by_user_id,
    get_user_by_id,
    get_user_by_telegram_id,
    set_room_available,
    set_room_reserved,
    set_user_admin,
    set_user_blocked,
    set_user_status,
    update_reservation_status,
)
from keyboards.user import ADMIN_PANEL_BUTTONS, build_main_menu
from states.admin import AdminManage

router = Router()


def is_config_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


async def is_admin(user_id: int) -> bool:
    if is_config_admin(user_id):
        return True

    user = await get_user_by_telegram_id(user_id)
    return bool(user and user["is_admin"])


def admin_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📋 Заявки на регистрацию",
                    callback_data="admin:pending_users",
                )
            ],
            [
                InlineKeyboardButton(
                    text="👥 Зарегистрированные",
                    callback_data="admin:registered_users",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏠 Заявки на бронь",
                    callback_data="admin:pending_reservations",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔒 Управление пользователями",
                    callback_data="admin:all_users",
                )
            ],
            [InlineKeyboardButton(text="🛡 Админы", callback_data="admin:admins")],
            [InlineKeyboardButton(text="📊 Статистика", callback_data="admin:stats")],
        ]
    )


def parse_telegram_id(message: Message) -> int | None:
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) != 2:
        return None

    return parse_telegram_id_value(parts[1])


def parse_telegram_id_value(value: str | None) -> int | None:
    value = (value or "").strip()
    if not value.isdigit():
        return None

    return int(value)


async def get_pending_users():
    all_users = await get_all_users()
    return [user for user in all_users if user["status"] == "pending"]


async def notify_user(bot, telegram_id: int, text: str, reply_markup=None):
    try:
        await bot.send_message(telegram_id, text, reply_markup=reply_markup)
    except Exception:
        pass


async def ensure_admin_message(message: Message) -> bool:
    if await is_admin(message.from_user.id):
        return True

    await message.answer("Доступ запрещен. Вы не администратор.")
    return False


async def ensure_admin_callback(callback: CallbackQuery) -> bool:
    if await is_admin(callback.from_user.id):
        return True

    await callback.answer("Доступ запрещен.", show_alert=True)
    return False


async def ensure_user_exists_by_telegram_id(telegram_id: int):
    await add_user(telegram_id)
    return await get_user_by_telegram_id(telegram_id)


def user_is_admin_row(user) -> bool:
    return bool(user and (user["telegram_id"] in ADMIN_IDS or user["is_admin"]))


def user_management_keyboard(user, back_callback: str) -> InlineKeyboardMarkup:
    block_text = "🔓 Разблокировать" if user["is_blocked"] else "🔒 Заблокировать"
    admin_text = "❌ Снять админа" if user_is_admin_row(user) else "🛡 Сделать админом"
    admin_callback = (
        f"admin:remove_admin:{user['id']}"
        if user_is_admin_row(user)
        else f"admin:add_admin:{user['id']}"
    )

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=block_text,
                    callback_data=f"admin:toggle_block:{user['id']}",
                )
            ],
            [InlineKeyboardButton(text=admin_text, callback_data=admin_callback)],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data=back_callback)],
        ]
    )


def user_detail_text(user) -> str:
    return (
        f"👤 ID: {user['id']}\n"
        f"Telegram: {user['telegram_id']}\n"
        f"Имя: {user['name'] or '-'}\n"
        f"Фамилия: {user['surname'] or '-'}\n"
        f"Город: {user['city'] or '-'}\n"
        f"Возраст: {user['age'] or '-'}\n"
        f"Специальность: {user['education'] or '-'}\n"
        f"Учебное заведение: {user['university'] or '-'}\n"
        f"Статус: {user['status']}\n"
        f"Админ: {'Да' if user_is_admin_row(user) else 'Нет'}\n"
        f"Заблокирован: {'Да' if user['is_blocked'] else 'Нет'}"
    )


@router.message(Command(commands=["admin"]))
@router.message(F.text.in_(ADMIN_PANEL_BUTTONS))
async def admin_menu(message: Message):
    if not await ensure_admin_message(message):
        return

    await message.answer("🔐 Админ-панель:", reply_markup=admin_menu_keyboard())


@router.message(Command(commands=["add_admin"]))
async def add_admin_cmd(message: Message):
    if not await ensure_admin_message(message):
        return

    telegram_id = parse_telegram_id(message)
    if telegram_id is None:
        await message.answer("Используйте так: /add_admin 123456789")
        return

    user = await ensure_user_exists_by_telegram_id(telegram_id)
    await set_user_admin(telegram_id, True)

    await message.answer(f"✅ Telegram ID {telegram_id} добавлен в админы.")
    await notify_user(
        message.bot,
        telegram_id,
        "✅ Вам выдали доступ к админ-панели.",
        reply_markup=build_main_menu(is_admin=True)
        if user and user["status"] == "registered"
        else None,
    )


@router.message(Command(commands=["remove_admin"]))
async def remove_admin_cmd(message: Message):
    if not await ensure_admin_message(message):
        return

    telegram_id = parse_telegram_id(message)
    if telegram_id is None:
        await message.answer("Используйте так: /remove_admin 123456789")
        return

    if telegram_id == message.from_user.id:
        await message.answer("Нельзя снять админку с самого себя.")
        return

    if is_config_admin(telegram_id):
        await message.answer("Нельзя снять админку с главного админа.")
        return

    user = await get_user_by_telegram_id(telegram_id)
    if not user:
        await message.answer("Пользователь с таким Telegram ID не найден в базе.")
        return

    await set_user_admin(telegram_id, False)
    await message.answer(f"✅ Telegram ID {telegram_id} больше не админ.")
    await notify_user(message.bot, telegram_id, "❌ У вас забрали доступ к админ-панели.")


@router.callback_query(F.data == "admin:add_admin_prompt")
async def admin_add_admin_prompt(callback: CallbackQuery, state: FSMContext):
    if not await ensure_admin_callback(callback):
        return

    await state.set_state(AdminManage.add_admin_id)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:admins")]
        ]
    )
    await callback.message.edit_text(
        "Введите Telegram ID пользователя, которому нужно выдать админку:",
        reply_markup=keyboard,
    )
    await callback.answer()


@router.message(AdminManage.add_admin_id)
async def admin_add_admin_from_message(message: Message, state: FSMContext):
    if not await ensure_admin_message(message):
        await state.clear()
        return

    telegram_id = parse_telegram_id_value(message.text)
    if telegram_id is None:
        await message.answer("Введите только Telegram ID числом, например: 123456789")
        return

    user = await ensure_user_exists_by_telegram_id(telegram_id)
    await set_user_admin(telegram_id, True)
    await state.clear()

    await message.answer(
        f"✅ Telegram ID {telegram_id} добавлен в админы.",
        reply_markup=admin_menu_keyboard(),
    )
    await notify_user(
        message.bot,
        telegram_id,
        "✅ Вам выдали доступ к админ-панели.",
        reply_markup=build_main_menu(is_admin=True)
        if user and user["status"] == "registered"
        else None,
    )


@router.callback_query(F.data == "admin:menu")
async def admin_back_to_menu(callback: CallbackQuery, state: FSMContext):
    if not await ensure_admin_callback(callback):
        return

    await state.clear()
    await callback.message.edit_text("🔐 Админ-панель:", reply_markup=admin_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data == "admin:admins")
async def admin_admins(callback: CallbackQuery, state: FSMContext):
    if not await ensure_admin_callback(callback):
        return

    await state.clear()
    users = await get_all_users()
    admin_users = [user for user in users if user_is_admin_row(user)]
    known_admin_ids = {user["telegram_id"] for user in admin_users}
    missing_config_admins = [
        admin_id for admin_id in ADMIN_IDS if admin_id not in known_admin_ids
    ]

    text = "🛡 Админы:\n\n"
    if admin_users:
        for user in admin_users:
            source = "главный админ" if user["telegram_id"] in ADMIN_IDS else "админ"
            text += (
                f"- {user['name'] or 'Без имени'} {user['surname'] or ''} "
                f"({user['telegram_id']}, {source})\n"
            )

    for admin_id in missing_config_admins:
        text += f"- Telegram ID {admin_id} (главный админ, не зарегистрирован в базе)\n"

    if not admin_users and not missing_config_admins:
        text += "Пока нет админов.\n"

    text += "\nДобавить или снять админа можно кнопками ниже."

    buttons = [[InlineKeyboardButton(text="➕ Добавить админа", callback_data="admin:add_admin_prompt")]]
    for user in admin_users:
        display = f"{user['name'] or 'Без имени'} {user['surname'] or ''} ({user['telegram_id']})"
        if user["telegram_id"] == callback.from_user.id or is_config_admin(user["telegram_id"]):
            buttons.append(
                [
                    InlineKeyboardButton(
                        text=f"👤 {display}",
                        callback_data=f"admin:detail_user:{user['id']}",
                    )
                ]
            )
        else:
            buttons.append(
                [
                    InlineKeyboardButton(
                        text=f"❌ Снять: {display}",
                        callback_data=f"admin:remove_admin:{user['id']}",
                    )
                ]
            )

    buttons.extend(
        [
            [InlineKeyboardButton(text="👥 Все пользователи", callback_data="admin:all_users")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:menu")],
        ]
    )
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=buttons
    )

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "admin:pending_users")
async def admin_pending_users(callback: CallbackQuery):
    if not await ensure_admin_callback(callback):
        return

    pending = await get_pending_users()
    if not pending:
        await callback.answer("Нет заявок на регистрацию.", show_alert=True)
        return

    buttons = []
    for user in pending:
        display = f"{user['name'] or 'Без имени'} {user['surname'] or ''} ({user['age'] or '?'} лет)"
        buttons.append(
            [
                InlineKeyboardButton(
                    text=display,
                    callback_data=f"admin:pend_user:{user['id']}",
                )
            ]
        )

    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:menu")])

    await callback.message.edit_text(
        "Заявки на регистрацию:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:pend_user:"))
async def admin_pending_user_detail(callback: CallbackQuery):
    if not await ensure_admin_callback(callback):
        return

    user_id = int(callback.data.split(":")[2])
    user = await get_user_by_id(user_id)
    if not user:
        await callback.answer("Пользователь не найден.", show_alert=True)
        return

    text = (
        "Заявка на регистрацию:\n\n"
        f"Имя: {user['name'] or '-'}\n"
        f"Фамилия: {user['surname'] or '-'}\n"
        f"Город: {user['city'] or '-'}\n"
        f"Возраст: {user['age'] or '-'}\n"
        f"Специальность: {user['education'] or '-'}\n"
        f"Учебное заведение: {user['university'] or '-'}\n"
        f"Telegram ID: {user['telegram_id']}"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Одобрить",
                    callback_data=f"admin:app_user:{user_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отклонить",
                    callback_data=f"admin:rej_user:{user_id}",
                )
            ],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:pending_users")],
        ]
    )

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


async def approve_user(callback: CallbackQuery, user_id: int):
    user = await get_user_by_id(user_id)
    if not user:
        await callback.answer("Пользователь не найден.", show_alert=True)
        return

    await set_user_status(user["telegram_id"], "registered")
    await callback.message.edit_text(f"✅ {user['name']} {user['surname']} одобрен(а).")
    await callback.answer("Пользователь одобрен.")

    await notify_user(
        callback.bot,
        user["telegram_id"],
        "✅ Ваша регистрация одобрена администратором. Добро пожаловать!",
        reply_markup=build_main_menu(is_admin=await is_admin(user["telegram_id"])),
    )


async def reject_user(callback: CallbackQuery, user_id: int):
    user = await get_user_by_id(user_id)
    if not user:
        await callback.answer("Пользователь не найден.", show_alert=True)
        return

    await set_user_status(user["telegram_id"], "rejected")
    await callback.message.edit_text(f"❌ {user['name']} {user['surname']} отклонен(а).")
    await callback.answer("Пользователь отклонен.")

    await notify_user(
        callback.bot,
        user["telegram_id"],
        "❌ Ваша заявка отклонена администратором. Для повторной регистрации отправьте /start.",
    )


@router.callback_query(F.data.startswith("admin:app_user:"))
async def admin_approve_user(callback: CallbackQuery):
    if not await ensure_admin_callback(callback):
        return

    user_id = int(callback.data.split(":")[2])
    await approve_user(callback, user_id)


@router.callback_query(F.data.startswith("admin:rej_user:"))
async def admin_reject_user(callback: CallbackQuery):
    if not await ensure_admin_callback(callback):
        return

    user_id = int(callback.data.split(":")[2])
    await reject_user(callback, user_id)


@router.callback_query(F.data.startswith("admin:user:"))
async def admin_legacy_user_decision(callback: CallbackQuery):
    if not await ensure_admin_callback(callback):
        return

    parts = callback.data.split(":")
    if len(parts) != 4:
        await callback.answer("Неверный формат кнопки.", show_alert=True)
        return

    user_id = int(parts[2])
    action = parts[3]

    if action == "approve":
        await approve_user(callback, user_id)
    elif action == "reject":
        await reject_user(callback, user_id)
    else:
        await callback.answer("Неизвестное действие.", show_alert=True)


@router.callback_query(F.data == "admin:registered_users")
async def admin_registered_users(callback: CallbackQuery):
    if not await ensure_admin_callback(callback):
        return

    users = await get_registered_users()
    if not users:
        await callback.answer("Нет зарегистрированных пользователей.", show_alert=True)
        return

    buttons = []
    for user in users:
        reservations = await get_reservations_by_user_id(user["id"])
        rented = [
            f"{res['dormitory_name']} {res['room_number']}"
            for res in reservations
            if res["status"] == "approved"
        ]
        rented_text = ", ".join(rented) if rented else "нет брони"
        admin_mark = " 🛡" if user_is_admin_row(user) else ""
        display = f"{user['name']} {user['surname']}{admin_mark} — {rented_text}"
        buttons.append(
            [
                InlineKeyboardButton(
                    text=display,
                    callback_data=f"admin:reg_user:{user['id']}",
                )
            ]
        )

    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:menu")])

    await callback.message.edit_text(
        "Зарегистрированные пользователи:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:reg_user:"))
async def admin_registered_user_detail(callback: CallbackQuery):
    if not await ensure_admin_callback(callback):
        return

    user_id = int(callback.data.split(":")[2])
    user = await get_user_by_id(user_id)
    if not user:
        await callback.answer("Пользователь не найден.", show_alert=True)
        return

    reservations = await get_reservations_by_user_id(user["id"])
    text = user_detail_text(user) + "\n\n📋 Бронирования:\n"

    if reservations:
        for reservation in reservations:
            text += (
                f"- {reservation['dormitory_name']} {reservation['room_number']} "
                f"({reservation['status']}) {reservation['price']} PLN\n"
            )
    else:
        text += "- нет бронирований\n"

    await callback.message.edit_text(
        text,
        reply_markup=user_management_keyboard(user, "admin:registered_users"),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:toggle_block:"))
async def admin_toggle_block(callback: CallbackQuery):
    if not await ensure_admin_callback(callback):
        return

    user_id = int(callback.data.split(":")[2])
    user = await get_user_by_id(user_id)
    if not user:
        await callback.answer("Пользователь не найден.", show_alert=True)
        return

    new_state = not bool(user["is_blocked"])
    if new_state and user["telegram_id"] == callback.from_user.id:
        await callback.answer("Нельзя заблокировать самого себя.", show_alert=True)
        return

    await set_user_blocked(user["telegram_id"], new_state)

    status_text = "заблокирован" if new_state else "разблокирован"
    await callback.message.edit_text(f"Пользователь {status_text}.")
    await callback.answer("Статус блокировки обновлен.")

    await notify_user(
        callback.bot,
        user["telegram_id"],
        f"Ваш аккаунт был {status_text} администратором.",
    )


@router.callback_query(F.data.startswith("admin:add_admin:"))
async def admin_add_admin_callback(callback: CallbackQuery):
    if not await ensure_admin_callback(callback):
        return

    user_id = int(callback.data.split(":")[2])
    user = await get_user_by_id(user_id)
    if not user:
        await callback.answer("Пользователь не найден.", show_alert=True)
        return

    await set_user_admin(user["telegram_id"], True)
    await callback.message.edit_text(f"✅ {user['telegram_id']} теперь админ.")
    await callback.answer("Админ добавлен.")

    await notify_user(
        callback.bot,
        user["telegram_id"],
        "✅ Вам выдали доступ к админ-панели.",
        reply_markup=build_main_menu(is_admin=True)
        if user["status"] == "registered"
        else None,
    )


@router.callback_query(F.data.startswith("admin:remove_admin:"))
async def admin_remove_admin_callback(callback: CallbackQuery):
    if not await ensure_admin_callback(callback):
        return

    user_id = int(callback.data.split(":")[2])
    user = await get_user_by_id(user_id)
    if not user:
        await callback.answer("Пользователь не найден.", show_alert=True)
        return

    if user["telegram_id"] == callback.from_user.id:
        await callback.answer("Нельзя снять админку с самого себя.", show_alert=True)
        return

    if is_config_admin(user["telegram_id"]):
        await callback.answer(
            "Нельзя снять админку с главного админа.",
            show_alert=True,
        )
        return

    await set_user_admin(user["telegram_id"], False)
    await callback.message.edit_text(f"✅ {user['telegram_id']} больше не админ.")
    await callback.answer("Админ снят.")

    await notify_user(callback.bot, user["telegram_id"], "❌ У вас забрали доступ к админ-панели.")


@router.callback_query(F.data == "admin:pending_reservations")
async def admin_pending_reservations(callback: CallbackQuery):
    if not await ensure_admin_callback(callback):
        return

    reservations = await get_pending_reservations()
    if not reservations:
        await callback.answer("Нет ожидающих заявок на бронь.", show_alert=True)
        return

    buttons = []
    for reservation in reservations:
        display = (
            f"#{reservation['id']} {reservation['name']} {reservation['surname']} "
            f"— {reservation['dormitory_name']} {reservation['room_number']}"
        )
        buttons.append(
            [
                InlineKeyboardButton(
                    text=display,
                    callback_data=f"admin:res:{reservation['id']}",
                )
            ]
        )

    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:menu")])

    await callback.message.edit_text(
        "Заявки на бронь:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:res:") & F.data.endswith(":approve"))
async def admin_approve_reservation(callback: CallbackQuery):
    if not await ensure_admin_callback(callback):
        return

    parts = callback.data.split(":")
    if len(parts) != 4:
        await callback.answer("Неверный формат кнопки.", show_alert=True)
        return

    reservation_id = int(parts[2])
    reservation = await get_reservation_by_id(reservation_id)
    if not reservation:
        await callback.answer("Заявка не найдена.", show_alert=True)
        return

    if reservation["status"] != "pending":
        await callback.answer("Эта заявка уже обработана.", show_alert=True)
        return

    await update_reservation_status(reservation_id, "approved")
    await set_room_reserved(reservation["room_id"])

    await callback.message.edit_text(f"✅ Заявка #{reservation_id} одобрена.")
    await callback.answer("Заявка одобрена.")

    await notify_user(
        callback.bot,
        reservation["telegram_id"],
        f"✅ Ваша заявка #{reservation_id} на бронь одобрена администратором!",
    )


@router.callback_query(F.data.startswith("admin:res:") & F.data.endswith(":reject"))
async def admin_reject_reservation(callback: CallbackQuery):
    if not await ensure_admin_callback(callback):
        return

    parts = callback.data.split(":")
    if len(parts) != 4:
        await callback.answer("Неверный формат кнопки.", show_alert=True)
        return

    reservation_id = int(parts[2])
    reservation = await get_reservation_by_id(reservation_id)
    if not reservation:
        await callback.answer("Заявка не найдена.", show_alert=True)
        return

    if reservation["status"] != "pending":
        await callback.answer("Эта заявка уже обработана.", show_alert=True)
        return

    await update_reservation_status(reservation_id, "rejected")
    await set_room_available(reservation["room_id"])

    await callback.message.edit_text(f"❌ Заявка #{reservation_id} отклонена.")
    await callback.answer("Заявка отклонена.")

    await notify_user(
        callback.bot,
        reservation["telegram_id"],
        f"❌ Ваша заявка #{reservation_id} на бронь отклонена администратором.",
    )


@router.callback_query(F.data.startswith("admin:res:"))
async def admin_reservation_detail(callback: CallbackQuery):
    if not await ensure_admin_callback(callback):
        return

    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.answer("Неверный формат кнопки.", show_alert=True)
        return

    reservation_id = int(parts[2])
    reservation = await get_reservation_by_id(reservation_id)
    if not reservation:
        await callback.answer("Заявка не найдена.", show_alert=True)
        return

    text = (
        f"Заявка на бронь #{reservation['id']}\n\n"
        f"Пользователь: {reservation['name']} {reservation['surname']}\n"
        f"Telegram ID: {reservation['telegram_id']}\n"
        f"Комната: {reservation['dormitory_name']} {reservation['room_number']}\n"
        f"Цена: {reservation['price']} PLN\n"
        f"Статус: {reservation['status']}\n"
        f"Дата создания: {reservation['created_at']}"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Одобрить",
                    callback_data=f"admin:res:{reservation_id}:approve",
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отклонить",
                    callback_data=f"admin:res:{reservation_id}:reject",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="admin:pending_reservations",
                )
            ],
        ]
    )

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "admin:all_users")
async def admin_all_users(callback: CallbackQuery):
    if not await ensure_admin_callback(callback):
        return

    users = await get_all_users()
    if not users:
        await callback.answer("Пользователей не найдено.", show_alert=True)
        return

    buttons = []
    for user in users:
        status_icon = "✅" if user["status"] == "registered" else "⏳" if user["status"] == "pending" else "❌"
        admin_mark = " 🛡" if user_is_admin_row(user) else ""
        blocked_mark = " 🚫" if user["is_blocked"] else ""
        display = (
            f"{status_icon} {user['name'] or 'Имя'} {user['surname'] or ''}"
            f"{admin_mark}{blocked_mark} — {user['status']}"
        )
        buttons.append(
            [
                InlineKeyboardButton(
                    text=display,
                    callback_data=f"admin:detail_user:{user['id']}",
                )
            ]
        )

    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:menu")])

    await callback.message.edit_text(
        "Все пользователи:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:detail_user:"))
async def admin_detail_user(callback: CallbackQuery):
    if not await ensure_admin_callback(callback):
        return

    user_id = int(callback.data.split(":")[2])
    user = await get_user_by_id(user_id)
    if not user:
        await callback.answer("Пользователь не найден.", show_alert=True)
        return

    await callback.message.edit_text(
        user_detail_text(user),
        reply_markup=user_management_keyboard(user, "admin:all_users"),
    )
    await callback.answer()


@router.callback_query(F.data == "admin:stats")
async def admin_stats(callback: CallbackQuery):
    if not await ensure_admin_callback(callback):
        return

    all_users = await get_all_users()
    registered_users = await get_registered_users()
    pending_users = await get_pending_users()
    pending_reservations = await get_pending_reservations()
    admin_ids = set(ADMIN_IDS)
    admin_ids.update(user["telegram_id"] for user in all_users if user["is_admin"])
    admin_count = len(admin_ids)

    text = (
        "📊 Статистика:\n\n"
        f"👥 Всего пользователей: {len(all_users)}\n"
        f"✅ Зарегистрировано: {len(registered_users)}\n"
        f"⏳ Ожидают одобрения: {len(pending_users)}\n"
        f"🏠 Ожидающих заявок на бронь: {len(pending_reservations)}\n"
        f"🛡 Админов: {admin_count}"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:menu")]
        ]
    )

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()
