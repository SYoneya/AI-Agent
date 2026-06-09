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
    add_issue,
    get_dormitories,
    get_dormitory_by_id,
    get_issue_by_id,
    get_user_by_telegram_id,
    is_user_blocked,
)
from keyboards.user import REPORT_ISSUE_BUTTONS, build_main_menu, contacts_menu
from states.issue import IssueForm

router = Router()

ISSUE_CATEGORIES = {
    "electricity": "🔌 Електрика",
    "water": "🚿 Водопостачання",
    "heating": "🔥 Опалення",
    "internet": "🛜 Інтернет",
    "cleaning": "🧹 Прибирання",
    "damage": "🪟 Пошкодження майна",
    "other": "❓ Інше",
}

SKIP_PHOTO_TEXT = "Пропустити фото"


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
            "🚫 Ваш акаунт заблоковано. Створення заявок недоступне.",
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
            "Ваш акаунт заблоковано. Створення заявок недоступне.",
            show_alert=True,
        )
        return False

    return True


def dormitories_keyboard(dormitories) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=dormitory["name"],
                    callback_data=f"issue:dorm:{dormitory['id']}",
                )
            ]
            for dormitory in dormitories
        ]
    )


def categories_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=label, callback_data=f"issue:cat:{key}")]
            for key, label in ISSUE_CATEGORIES.items()
        ]
    )


def skip_photo_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=SKIP_PHOTO_TEXT)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


async def notify_admins_about_issue(bot, issue_id: int):
    issue = await get_issue_by_id(issue_id)
    if not issue:
        return

    text = (
        f"⚠️ Нова проблема #{issue['id']}\n\n"
        f"Користувач: {issue['name']} {issue['surname']}\n"
        f"Гуртожиток: {issue['dormitory_name']}\n"
        f"Категорія: {issue['category']}\n"
        f"Опис: {issue['description']}\n"
        f"Статус: 🟡 Нова"
    )
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Відкрити заявку",
                    callback_data=f"admin:issue:{issue_id}",
                )
            ]
        ]
    )

    for admin_id in ADMIN_IDS:
        try:
            if issue["photo_file_id"]:
                await bot.send_photo(
                    admin_id,
                    photo=issue["photo_file_id"],
                    caption=text,
                    reply_markup=keyboard,
                )
            else:
                await bot.send_message(admin_id, text, reply_markup=keyboard)
        except Exception:
            pass


@router.message(F.text.in_(REPORT_ISSUE_BUTTONS))
async def issue_start(message: Message, state: FSMContext):
    if not await ensure_registered_message(message):
        return

    await state.clear()
    dormitories = await get_dormitories()
    await state.set_state(IssueForm.dormitory)
    await message.answer(
        "Який гуртожиток?",
        reply_markup=dormitories_keyboard(dormitories),
    )


@router.callback_query(IssueForm.dormitory, F.data.startswith("issue:dorm:"))
async def issue_get_dormitory(callback: CallbackQuery, state: FSMContext):
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
    await state.set_state(IssueForm.category)
    await callback.message.edit_text(
        f"Гуртожиток: {dormitory['name']}\n\nОберіть тип проблеми:",
        reply_markup=categories_keyboard(),
    )
    await callback.answer()


@router.callback_query(IssueForm.category, F.data.startswith("issue:cat:"))
async def issue_get_category(callback: CallbackQuery, state: FSMContext):
    category_key = callback.data.split(":")[2]
    category = ISSUE_CATEGORIES.get(category_key)
    if not category:
        await callback.answer("Категорію не знайдено.", show_alert=True)
        return

    await state.update_data(category=category)
    await state.set_state(IssueForm.description)
    await callback.message.edit_text(
        f"Категорія: {category}\n\nОпишіть проблему:"
    )
    await callback.answer()


@router.message(IssueForm.description, F.text)
async def issue_get_description(message: Message, state: FSMContext):
    description = message.text.strip()
    if len(description) < 5:
        await message.answer("Опишіть проблему трохи детальніше:")
        return

    await state.update_data(description=description)
    await state.set_state(IssueForm.photo)
    await message.answer(
        "Додайте фото проблеми або натисніть «Пропустити фото».",
        reply_markup=skip_photo_keyboard(),
    )


@router.message(IssueForm.photo)
async def issue_get_photo(message: Message, state: FSMContext):
    if message.photo:
        photo_file_id = message.photo[-1].file_id
    elif message.text and message.text.strip() == SKIP_PHOTO_TEXT:
        photo_file_id = None
    else:
        await message.answer(
            "Надішліть фото або натисніть «Пропустити фото».",
            reply_markup=skip_photo_keyboard(),
        )
        return

    user = await get_user_by_telegram_id(message.from_user.id)
    data = await state.get_data()
    issue_id = await add_issue(
        user["id"],
        data["dormitory_id"],
        data["category"],
        data["description"],
        photo_file_id,
    )
    await state.clear()

    await message.answer(
        f"✅ Заявка #{issue_id} створена.\nСтатус: 🟡 Нова",
        reply_markup=ReplyKeyboardRemove(),
    )
    await message.answer(
        "Дякуємо, адміністрація отримає повідомлення.",
        reply_markup=build_main_menu(
            is_admin=bool(user["telegram_id"] in ADMIN_IDS or user["is_admin"])
        ),
    )
    await notify_admins_about_issue(message.bot, issue_id)
