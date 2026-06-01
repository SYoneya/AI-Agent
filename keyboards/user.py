from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

DORMITORIES_BUTTON = "🏠 Akademiki"
PROFILE_BUTTON = "👤 Profil"
MY_REQUESTS_BUTTON = "📄 Мои заявки"
CONTACTS_BUTTON = "📞 Контакты"
ADMIN_PANEL_BUTTON = "🔐 Админ-панель"

DORMITORIES_BUTTONS = (DORMITORIES_BUTTON, "Akademiki")
PROFILE_BUTTONS = (PROFILE_BUTTON, "Profil", " Profil", "Профиль")
MY_REQUESTS_BUTTONS = (MY_REQUESTS_BUTTON, "Мои заявки")
CONTACTS_BUTTONS = (CONTACTS_BUTTON, "Контакты")
ADMIN_PANEL_BUTTONS = (ADMIN_PANEL_BUTTON, "Админ-панель")


def build_main_menu(is_admin: bool = False) -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text=DORMITORIES_BUTTON)],
        [
            KeyboardButton(text=PROFILE_BUTTON),
            KeyboardButton(text=MY_REQUESTS_BUTTON),
        ],
        [KeyboardButton(text=CONTACTS_BUTTON)],
    ]

    if is_admin:
        keyboard.append([KeyboardButton(text=ADMIN_PANEL_BUTTON)])

    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


main_menu = build_main_menu()

contacts_menu = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text=CONTACTS_BUTTON)]],
    resize_keyboard=True,
)
