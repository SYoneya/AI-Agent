from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from config import ADMIN_IDS, ADMIN_USERNAME, CONTACT_EMAIL, CONTACT_PHONE
from database.db import (
    get_user_by_telegram_id,
    is_user_blocked,
    update_user_profile_field,
)
from keyboards.user import (
    CONTACTS_BUTTONS,
    PROFILE_BUTTONS,
    build_main_menu,
    contacts_menu,
)
from states.profile_edit import ProfileEdit

router = Router()


FIELD_TITLES = {
    "city": "Город",
    "age": "Возраст",
    "education": "Специальность",
    "university": "Учебное заведение",
}


def user_is_admin(user) -> bool:
    return bool(user and (user["telegram_id"] in ADMIN_IDS or user["is_admin"]))


def build_profile_text(user) -> str:
    admin_line = "Админ: Да\n" if user_is_admin(user) else ""
    return (
        "👤 Профиль\n\n"
        f"ID: {user['telegram_id']}\n"
        f"Имя: {user['name'] or '-'}\n"
        f"Фамилия: {user['surname'] or '-'}\n"
        f"Город: {user['city'] or '-'}\n"
        f"Возраст: {user['age'] or '-'}\n"
        f"Специальность: {user['education'] or '-'}\n"
        f"Учебное заведение: {user['university'] or '-'}\n"
        f"Статус: {user['status']}\n"
        f"Заблокирован: {'Да' if user['is_blocked'] else 'Нет'}\n"
        f"{admin_line}"
    )


def profile_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✏️ Изменить данные",
                    callback_data="edit:profile",
                )
            ],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back:menu")],
        ]
    )


async def answer_registered_only(message: Message):
    await message.answer(
        "Эта функция доступна только после одобрения регистрации.",
        reply_markup=contacts_menu,
    )


@router.message(F.text.in_(PROFILE_BUTTONS))
async def profile(message: Message):
    user = await get_user_by_telegram_id(message.from_user.id)

    if not user or user["status"] != "registered":
        await answer_registered_only(message)
        return

    if await is_user_blocked(message.from_user.id):
        await message.answer(
            "🚫 Ваш аккаунт заблокирован. Вы не можете просматривать профиль.",
            reply_markup=contacts_menu,
        )
        return

    await message.answer(build_profile_text(user), reply_markup=profile_keyboard())


@router.message(F.text.in_(CONTACTS_BUTTONS))
async def contacts(message: Message):
    await message.answer(
        "📞 Контакты:\n"
        f"Администратор: {ADMIN_USERNAME}\n"
        f"Email: {CONTACT_EMAIL}\n"
        f"Телефон: {CONTACT_PHONE}"
    )


@router.callback_query(F.data == "edit:profile")
async def edit_profile_callback(callback: CallbackQuery, state: FSMContext):
    user = await get_user_by_telegram_id(callback.from_user.id)

    if not user or user["status"] != "registered":
        await callback.answer(
            "Эта функция доступна только после одобрения регистрации.",
            show_alert=True,
        )
        return

    await callback.message.edit_text(
        "Выберите, что хотите изменить:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Город", callback_data="edit:city")],
                [InlineKeyboardButton(text="Возраст", callback_data="edit:age")],
                [
                    InlineKeyboardButton(
                        text="Специальность",
                        callback_data="edit:education",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="Учебное заведение",
                        callback_data="edit:university",
                    )
                ],
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="back:profile")],
            ]
        ),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("edit:"))
async def handle_edit(callback: CallbackQuery, state: FSMContext):
    user = await get_user_by_telegram_id(callback.from_user.id)

    if not user or user["status"] != "registered":
        await callback.answer(
            "Эта функция доступна только после одобрения регистрации.",
            show_alert=True,
        )
        return

    field = callback.data.split(":", 1)[1]
    if field not in FIELD_TITLES:
        await callback.answer("Неизвестное поле.", show_alert=True)
        return

    await state.update_data(edit_field=field)
    await callback.message.edit_text(f"Введите новое значение: {FIELD_TITLES[field]}")
    await state.set_state(ProfileEdit.waiting)
    await callback.answer()


@router.message(ProfileEdit.waiting)
async def save_profile_field(message: Message, state: FSMContext):
    user = await get_user_by_telegram_id(message.from_user.id)
    if not user or user["status"] != "registered":
        await state.clear()
        await answer_registered_only(message)
        return

    data = await state.get_data()
    field = data.get("edit_field")
    value = message.text.strip()

    if field == "age":
        try:
            value = int(value)
        except ValueError:
            await message.answer("Пожалуйста, введите возраст числом:")
            return

        if value < 14 or value > 100:
            await message.answer("Пожалуйста, введите реальный возраст:")
            return

    if field not in FIELD_TITLES:
        await state.clear()
        await message.answer("Не удалось определить поле для изменения.")
        return

    await update_user_profile_field(message.from_user.id, field, value)
    await state.clear()

    updated_user = await get_user_by_telegram_id(message.from_user.id)
    await message.answer(
        "✅ Данные обновлены.\n\n" + build_profile_text(updated_user),
        reply_markup=profile_keyboard(),
    )


@router.callback_query(F.data == "back:profile")
async def back_to_profile(callback: CallbackQuery):
    user = await get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("Пользователь не найден.", show_alert=True)
        return

    await callback.message.edit_text(build_profile_text(user), reply_markup=profile_keyboard())
    await callback.answer()


@router.callback_query(F.data == "back:menu")
async def back_to_menu(callback: CallbackQuery):
    user = await get_user_by_telegram_id(callback.from_user.id)
    if not user or user["status"] != "registered":
        await callback.message.answer("Доступны только контакты.", reply_markup=contacts_menu)
        await callback.answer()
        return

    await callback.message.answer(
        "Главное меню:",
        reply_markup=build_main_menu(is_admin=user_is_admin(user)),
    )
    await callback.answer()
