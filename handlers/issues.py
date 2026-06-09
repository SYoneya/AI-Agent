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
from keyboards.user import (
    REPORT_ISSUE_BUTTONS,
    build_contacts_menu,
    build_main_menu,
)
from locales import all_texts, language_from_user, t
from states.issue import IssueForm

router = Router()

ISSUE_CATEGORY_LABELS = {
    "uk": {
        "electricity": "🔌 Електрика",
        "water": "🚿 Водопостачання",
        "heating": "🔥 Опалення",
        "internet": "🛜 Інтернет",
        "cleaning": "🧹 Прибирання",
        "damage": "🪟 Пошкодження майна",
        "other": "❓ Інше",
    },
    "en": {
        "electricity": "🔌 Electricity",
        "water": "🚿 Water supply",
        "heating": "🔥 Heating",
        "internet": "🛜 Internet",
        "cleaning": "🧹 Cleaning",
        "damage": "🪟 Property damage",
        "other": "❓ Other",
    },
    "pl": {
        "electricity": "🔌 Elektryczność",
        "water": "🚿 Woda",
        "heating": "🔥 Ogrzewanie",
        "internet": "🛜 Internet",
        "cleaning": "🧹 Sprzątanie",
        "damage": "🪟 Uszkodzenie mienia",
        "other": "❓ Inne",
    },
}

ISSUE_TEXTS = {
    "uk": {
        "blocked": "🚫 Ваш акаунт заблоковано. Створення заявок недоступне.",
        "choose_dorm": "Який гуртожиток?",
        "dorm_not_found": "Гуртожиток не знайдено.",
        "choose_category": "Гуртожиток: {dormitory}\n\nОберіть тип проблеми:",
        "category_not_found": "Категорію не знайдено.",
        "describe": "Категорія: {category}\n\nОпишіть проблему:",
        "describe_more": "Опишіть проблему трохи детальніше:",
        "add_photo": "Додайте фото проблеми або натисніть «Пропустити фото».",
        "send_photo": "Надішліть фото або натисніть «Пропустити фото».",
        "created": "✅ Заявка #{id} створена.\nСтатус: 🟡 Нова",
        "thanks": "Дякуємо, адміністрація отримає повідомлення.",
    },
    "en": {
        "blocked": "🚫 Your account is blocked. Creating requests is unavailable.",
        "choose_dorm": "Which dormitory?",
        "dorm_not_found": "Dormitory not found.",
        "choose_category": "Dormitory: {dormitory}\n\nChoose the problem type:",
        "category_not_found": "Category not found.",
        "describe": "Category: {category}\n\nDescribe the problem:",
        "describe_more": "Describe the problem in a little more detail:",
        "add_photo": "Add a photo of the problem or tap “Skip photo”.",
        "send_photo": "Send a photo or tap “Skip photo”.",
        "created": "✅ Request #{id} created.\nStatus: 🟡 New",
        "thanks": "Thank you, the administration will receive a notification.",
    },
    "pl": {
        "blocked": "🚫 Twoje konto jest zablokowane. Tworzenie zgłoszeń jest niedostępne.",
        "choose_dorm": "Który akademik?",
        "dorm_not_found": "Nie znaleziono akademika.",
        "choose_category": "Akademik: {dormitory}\n\nWybierz typ problemu:",
        "category_not_found": "Nie znaleziono kategorii.",
        "describe": "Kategoria: {category}\n\nOpisz problem:",
        "describe_more": "Opisz problem trochę dokładniej:",
        "add_photo": "Dodaj zdjęcie problemu albo kliknij „Pomiń zdjęcie”.",
        "send_photo": "Wyślij zdjęcie albo kliknij „Pomiń zdjęcie”.",
        "created": "✅ Zgłoszenie #{id} utworzone.\nStatus: 🟡 Nowe",
        "thanks": "Dziękujemy, administracja otrzyma powiadomienie.",
    },
}

SKIP_PHOTO_TEXTS = all_texts("btn_skip_photo")


def it(language: str, key: str, **kwargs) -> str:
    value = ISSUE_TEXTS.get(language, ISSUE_TEXTS["uk"]).get(key, ISSUE_TEXTS["uk"][key])
    return value.format(**kwargs) if kwargs else value


def category_label(language: str, key: str) -> str | None:
    return ISSUE_CATEGORY_LABELS.get(language, ISSUE_CATEGORY_LABELS["uk"]).get(key)


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
            it(language, "blocked"),
            reply_markup=build_contacts_menu(language),
        )
        return False

    return True


async def ensure_registered_callback(callback: CallbackQuery) -> bool:
    user = await get_user_by_telegram_id(callback.from_user.id)
    language = language_from_user(user)
    if not user or user["status"] != "registered":
        await callback.answer(t(language, "auth_required"), show_alert=True)
        return False

    if await is_user_blocked(callback.from_user.id):
        await callback.answer(it(language, "blocked"), show_alert=True)
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


def categories_keyboard(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=label, callback_data=f"issue:cat:{key}")]
            for key, label in ISSUE_CATEGORY_LABELS.get(language, ISSUE_CATEGORY_LABELS["uk"]).items()
        ]
    )


def skip_photo_keyboard(language: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t(language, "btn_skip_photo"))]],
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

    user = await get_user_by_telegram_id(message.from_user.id)
    language = language_from_user(user)
    await state.clear()
    dormitories = await get_dormitories()
    await state.set_state(IssueForm.dormitory)
    await message.answer(
        it(language, "choose_dorm"),
        reply_markup=dormitories_keyboard(dormitories),
    )


@router.callback_query(IssueForm.dormitory, F.data.startswith("issue:dorm:"))
async def issue_get_dormitory(callback: CallbackQuery, state: FSMContext):
    if not await ensure_registered_callback(callback):
        return

    user = await get_user_by_telegram_id(callback.from_user.id)
    language = language_from_user(user)
    dormitory_id = int(callback.data.split(":")[2])
    dormitory = await get_dormitory_by_id(dormitory_id)
    if not dormitory:
        await callback.answer(it(language, "dorm_not_found"), show_alert=True)
        return

    await state.update_data(
        dormitory_id=dormitory["id"],
        dormitory_name=dormitory["name"],
    )
    await state.set_state(IssueForm.category)
    await callback.message.edit_text(
        it(language, "choose_category", dormitory=dormitory["name"]),
        reply_markup=categories_keyboard(language),
    )
    await callback.answer()


@router.callback_query(IssueForm.category, F.data.startswith("issue:cat:"))
async def issue_get_category(callback: CallbackQuery, state: FSMContext):
    user = await get_user_by_telegram_id(callback.from_user.id)
    language = language_from_user(user)
    category_key = callback.data.split(":")[2]
    category = category_label(language, category_key)
    if not category:
        await callback.answer(it(language, "category_not_found"), show_alert=True)
        return

    await state.update_data(category=category)
    await state.set_state(IssueForm.description)
    await callback.message.edit_text(it(language, "describe", category=category))
    await callback.answer()


@router.message(IssueForm.description, F.text)
async def issue_get_description(message: Message, state: FSMContext):
    user = await get_user_by_telegram_id(message.from_user.id)
    language = language_from_user(user)
    description = message.text.strip()
    if len(description) < 5:
        await message.answer(it(language, "describe_more"))
        return

    await state.update_data(description=description)
    await state.set_state(IssueForm.photo)
    await message.answer(
        it(language, "add_photo"),
        reply_markup=skip_photo_keyboard(language),
    )


@router.message(IssueForm.photo)
async def issue_get_photo(message: Message, state: FSMContext):
    user = await get_user_by_telegram_id(message.from_user.id)
    language = language_from_user(user)
    if message.photo:
        photo_file_id = message.photo[-1].file_id
    elif message.text and message.text.strip() in SKIP_PHOTO_TEXTS:
        photo_file_id = None
    else:
        await message.answer(
            it(language, "send_photo"),
            reply_markup=skip_photo_keyboard(language),
        )
        return

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
        it(language, "created", id=issue_id),
        reply_markup=ReplyKeyboardRemove(),
    )
    await message.answer(
        it(language, "thanks"),
        reply_markup=build_main_menu(
            language,
            is_admin=bool(user["telegram_id"] in ADMIN_IDS or user["is_admin"]),
        ),
    )
    await notify_admins_about_issue(message.bot, issue_id)
