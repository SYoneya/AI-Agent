from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from locales import LANGUAGE_CHOICES, all_texts, normalize_language, t

RESERVATION_BUTTONS = all_texts("btn_reservation")
DORMITORIES_BUTTONS = all_texts("btn_dormitories")
REPORT_ISSUE_BUTTONS = all_texts("btn_issue")
MY_REQUESTS_BUTTONS = all_texts("btn_requests")
INFO_BUTTONS = all_texts("btn_info")
CONTACTS_BUTTONS = all_texts("btn_contacts")
ADMIN_PANEL_BUTTONS = (*all_texts("btn_admin"), "/admin")

STUDENT_WSG_TEXTS = all_texts("student_wsg")
NON_STUDENT_WSG_TEXTS = all_texts("non_student_wsg")

# Backward-compatible defaults for imports that expect a single label.
RESERVATION_BUTTON = t("uk", "btn_reservation")
DORMITORIES_BUTTON = t("uk", "btn_dormitories")
REPORT_ISSUE_BUTTON = t("uk", "btn_issue")
MY_REQUESTS_BUTTON = t("uk", "btn_requests")
INFO_BUTTON = t("uk", "btn_info")
ADMIN_PANEL_BUTTON = t("uk", "btn_admin")
CONTACTS_BUTTON = t("uk", "btn_contacts")
STUDENT_WSG_TEXT = t("uk", "student_wsg")
NON_STUDENT_WSG_TEXT = t("uk", "non_student_wsg")


def build_language_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=label)] for label in LANGUAGE_CHOICES],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def build_main_menu(language: str = "uk", is_admin: bool = False) -> ReplyKeyboardMarkup:
    language = normalize_language(language)
    keyboard = [
        [KeyboardButton(text=t(language, "btn_reservation"))],
        [
            KeyboardButton(text=t(language, "btn_dormitories")),
            KeyboardButton(text=t(language, "btn_issue")),
        ],
        [
            KeyboardButton(text=t(language, "btn_requests")),
            KeyboardButton(text=t(language, "btn_info")),
        ],
    ]

    if is_admin:
        keyboard.append([KeyboardButton(text=t(language, "btn_admin"))])

    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def build_status_menu(language: str = "uk") -> ReplyKeyboardMarkup:
    language = normalize_language(language)
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t(language, "student_wsg"))],
            [KeyboardButton(text=t(language, "non_student_wsg"))],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def build_contacts_menu(language: str = "uk") -> ReplyKeyboardMarkup:
    language = normalize_language(language)
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t(language, "btn_contacts"))]],
        resize_keyboard=True,
    )


main_menu = build_main_menu()
contacts_menu = build_contacts_menu()
