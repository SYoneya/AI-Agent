from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

RESERVATION_BUTTON = "🏠 Резервація місця"
DORMITORIES_BUTTON = "🏢 Гуртожитки"
REPORT_ISSUE_BUTTON = "⚠️ Повідомити про проблему"
MY_REQUESTS_BUTTON = "📋 Мої заявки"
INFO_BUTTON = "ℹ️ Інформація"
ADMIN_PANEL_BUTTON = "🔐 Адмін-панель"
CONTACTS_BUTTON = "📞 Контакти"

STUDENT_WSG_TEXT = "Студент WSG"
NON_STUDENT_WSG_TEXT = "Не студент WSG"

DORMITORIES_BUTTONS = (DORMITORIES_BUTTON, "Гуртожитки")
RESERVATION_BUTTONS = (RESERVATION_BUTTON, "Резервація місця")
REPORT_ISSUE_BUTTONS = (REPORT_ISSUE_BUTTON, "Повідомити про проблему")
MY_REQUESTS_BUTTONS = (MY_REQUESTS_BUTTON, "Мої заявки")
INFO_BUTTONS = (INFO_BUTTON, "Інформація")
CONTACTS_BUTTONS = (CONTACTS_BUTTON, "Контакти")
ADMIN_PANEL_BUTTONS = (ADMIN_PANEL_BUTTON, "Адмін-панель", "/admin")


def build_main_menu(is_admin: bool = False) -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text=RESERVATION_BUTTON)],
        [KeyboardButton(text=DORMITORIES_BUTTON), KeyboardButton(text=REPORT_ISSUE_BUTTON)],
        [KeyboardButton(text=MY_REQUESTS_BUTTON), KeyboardButton(text=INFO_BUTTON)],
    ]

    if is_admin:
        keyboard.append([KeyboardButton(text=ADMIN_PANEL_BUTTON)])

    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def build_status_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=STUDENT_WSG_TEXT)],
            [KeyboardButton(text=NON_STUDENT_WSG_TEXT)],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


main_menu = build_main_menu()

contacts_menu = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text=CONTACTS_BUTTON)]],
    resize_keyboard=True,
)
