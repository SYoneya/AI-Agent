from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from config import ADMIN_IDS
from database.db import get_user_by_telegram_id, update_user
from keyboards.user import contacts_menu
from states.registration import Registration

router = Router()


@router.message(Registration.name)
async def get_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await message.answer("Введите фамилию:")
    await state.set_state(Registration.surname)


@router.message(Registration.surname)
async def get_surname(message: Message, state: FSMContext):
    await state.update_data(surname=message.text.strip())
    await message.answer("Введите город:")
    await state.set_state(Registration.city)


@router.message(Registration.city)
async def get_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text.strip())
    await message.answer("Введите ваш возраст:")
    await state.set_state(Registration.age)


@router.message(Registration.age)
async def get_age(message: Message, state: FSMContext):
    try:
        age = int(message.text)
    except ValueError:
        await message.answer("Пожалуйста, введите возраст числом:")
        return

    if age < 14 or age > 100:
        await message.answer("Пожалуйста, введите реальный возраст:")
        return

    await state.update_data(age=age)
    await message.answer("Введите вашу специальность или область обучения:")
    await state.set_state(Registration.education)


@router.message(Registration.education)
async def get_education(message: Message, state: FSMContext):
    await state.update_data(education=message.text.strip())
    await message.answer("Введите название вашего учебного заведения:")
    await state.set_state(Registration.university)


@router.message(Registration.university)
async def get_university(message: Message, state: FSMContext):
    await state.update_data(university=message.text.strip())
    data = await state.get_data()

    await update_user(
        message.from_user.id,
        data["name"],
        data["surname"],
        data["city"],
        data.get("age"),
        data.get("education"),
        data.get("university"),
    )

    user = await get_user_by_telegram_id(message.from_user.id)

    await message.answer(
        "✅ Заявка на регистрацию отправлена администратору. Ожидайте одобрения.",
        reply_markup=contacts_menu,
    )

    admin_target = ADMIN_IDS[0] if ADMIN_IDS else None
    if admin_target and user:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Одобрить",
                        callback_data=f"admin:app_user:{user['id']}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ Отклонить",
                        callback_data=f"admin:rej_user:{user['id']}",
                    )
                ],
            ]
        )

        await message.bot.send_message(
            admin_target,
            "Новая заявка на регистрацию:\n\n"
            f"ID: {user['id']}\n"
            f"Telegram ID: {user['telegram_id']}\n"
            f"Имя: {user['name']}\n"
            f"Фамилия: {user['surname']}\n"
            f"Город: {user['city']}\n"
            f"Возраст: {user['age']}\n"
            f"Специальность: {user['education']}\n"
            f"Учебное заведение: {user['university']}",
            reply_markup=keyboard,
        )

    await state.clear()
