DEFAULT_LANGUAGE = "uk"

LANGUAGE_LABELS = {
    "uk": "Українська",
    "en": "English",
    "pl": "Polski",
}

LANGUAGE_CHOICES = {
    "🇺🇦 Українська": "uk",
    "🇬🇧 English": "en",
    "🇵🇱 Polski": "pl",
}

TEXTS = {
    "uk": {
        "choose_language": "Оберіть мову:",
        "language_saved": "✅ Мову збережено.",
        "welcome": (
            "👋 Вітаємо в боті гуртожитків WSG!\n\n"
            "Для першого запуску потрібно пройти коротку авторизацію.\n"
            "Введіть ваше ім'я:"
        ),
        "blocked": "🚫 Ваш акаунт заблоковано. Зверніться до адміністрації.",
        "hello_menu": "Вітаю, {name}! 👋\nОберіть дію в головному меню.",
        "main_menu": "Головне меню:",
        "auth_required": "Ця функція доступна після авторизації. Надішліть /start.",
        "feature_blocked": "🚫 Ваш акаунт заблоковано. Функція недоступна.",
        "enter_name_full": "Введіть ім'я повністю:",
        "enter_surname": "Введіть ваше прізвище:",
        "enter_surname_full": "Введіть прізвище повністю:",
        "enter_phone": "Введіть номер телефону:",
        "enter_phone_valid": "Введіть коректний номер телефону:",
        "enter_email": "Введіть email:",
        "enter_email_valid": "Введіть коректний email:",
        "choose_status": "Оберіть ваш статус:",
        "choose_option": "Оберіть один із запропонованих варіантів:",
        "registration_done": (
            "✅ Авторизацію завершено.\n"
            "Тепер ви можете бронювати місце, переглядати гуртожитки та створювати заявки."
        ),
        "student_wsg": "Студент WSG",
        "non_student_wsg": "Не студент WSG",
        "btn_reservation": "🏠 Резервація місця",
        "btn_dormitories": "🏢 Гуртожитки",
        "btn_issue": "⚠️ Повідомити про проблему",
        "btn_requests": "📋 Мої заявки",
        "btn_info": "ℹ️ Інформація",
        "btn_admin": "🔐 Адмін-панель",
        "btn_contacts": "📞 Контакти",
        "btn_skip_photo": "Пропустити фото",
        "room_single": "Одномісна",
        "room_double": "Двомісна",
        "room_triple": "Тримісна",
        "room_any": "Будь-яка",
        "status_student": "Студент WSG",
        "status_non_student": "Не студент WSG",
    },
    "en": {
        "choose_language": "Choose a language:",
        "language_saved": "✅ Language saved.",
        "welcome": (
            "👋 Welcome to the WSG dormitory bot!\n\n"
            "Please complete a short authorization first.\n"
            "Enter your first name:"
        ),
        "blocked": "🚫 Your account is blocked. Please contact the administration.",
        "hello_menu": "Hello, {name}! 👋\nChoose an action from the main menu.",
        "main_menu": "Main menu:",
        "auth_required": "This feature is available after authorization. Send /start.",
        "feature_blocked": "🚫 Your account is blocked. This feature is unavailable.",
        "enter_name_full": "Enter your full first name:",
        "enter_surname": "Enter your surname:",
        "enter_surname_full": "Enter your full surname:",
        "enter_phone": "Enter your phone number:",
        "enter_phone_valid": "Enter a valid phone number:",
        "enter_email": "Enter your email:",
        "enter_email_valid": "Enter a valid email:",
        "choose_status": "Choose your status:",
        "choose_option": "Choose one of the suggested options:",
        "registration_done": (
            "✅ Authorization completed.\n"
            "You can now reserve a place, view dormitories, and create requests."
        ),
        "student_wsg": "WSG student",
        "non_student_wsg": "Not a WSG student",
        "btn_reservation": "🏠 Reservation",
        "btn_dormitories": "🏢 Dormitories",
        "btn_issue": "⚠️ Report a problem",
        "btn_requests": "📋 My requests",
        "btn_info": "ℹ️ Information",
        "btn_admin": "🔐 Admin panel",
        "btn_contacts": "📞 Contacts",
        "btn_skip_photo": "Skip photo",
        "room_single": "Single room",
        "room_double": "Double room",
        "room_triple": "Triple room",
        "room_any": "Any room",
        "status_student": "WSG student",
        "status_non_student": "Not a WSG student",
    },
    "pl": {
        "choose_language": "Wybierz język:",
        "language_saved": "✅ Język zapisany.",
        "welcome": (
            "👋 Witamy w bocie akademików WSG!\n\n"
            "Najpierw przejdź krótką autoryzację.\n"
            "Podaj imię:"
        ),
        "blocked": "🚫 Twoje konto jest zablokowane. Skontaktuj się z administracją.",
        "hello_menu": "Witaj, {name}! 👋\nWybierz działanie z menu głównego.",
        "main_menu": "Menu główne:",
        "auth_required": "Ta funkcja jest dostępna po autoryzacji. Wyślij /start.",
        "feature_blocked": "🚫 Twoje konto jest zablokowane. Funkcja jest niedostępna.",
        "enter_name_full": "Podaj pełne imię:",
        "enter_surname": "Podaj nazwisko:",
        "enter_surname_full": "Podaj pełne nazwisko:",
        "enter_phone": "Podaj numer telefonu:",
        "enter_phone_valid": "Podaj poprawny numer telefonu:",
        "enter_email": "Podaj email:",
        "enter_email_valid": "Podaj poprawny email:",
        "choose_status": "Wybierz swój status:",
        "choose_option": "Wybierz jedną z proponowanych opcji:",
        "registration_done": (
            "✅ Autoryzacja zakończona.\n"
            "Możesz teraz rezerwować miejsce, przeglądać akademiki i tworzyć zgłoszenia."
        ),
        "student_wsg": "Student WSG",
        "non_student_wsg": "Nie jestem studentem WSG",
        "btn_reservation": "🏠 Rezerwacja miejsca",
        "btn_dormitories": "🏢 Akademiki",
        "btn_issue": "⚠️ Zgłoś problem",
        "btn_requests": "📋 Moje zgłoszenia",
        "btn_info": "ℹ️ Informacje",
        "btn_admin": "🔐 Panel administracyjny",
        "btn_contacts": "📞 Kontakty",
        "btn_skip_photo": "Pomiń zdjęcie",
        "room_single": "Jednoosobowy",
        "room_double": "Dwuosobowy",
        "room_triple": "Trzyosobowy",
        "room_any": "Dowolny",
        "status_student": "Student WSG",
        "status_non_student": "Nie jestem studentem WSG",
    },
}


def normalize_language(language: str | None) -> str:
    return language if language in TEXTS else DEFAULT_LANGUAGE


def language_from_user(user) -> str:
    if not user:
        return DEFAULT_LANGUAGE
    try:
        return normalize_language(user["language"])
    except (KeyError, IndexError):
        return DEFAULT_LANGUAGE


def t(language: str | None, key: str, **kwargs) -> str:
    language = normalize_language(language)
    value = TEXTS[language].get(key, TEXTS[DEFAULT_LANGUAGE].get(key, key))
    return value.format(**kwargs) if kwargs else value


def all_texts(key: str) -> tuple[str, ...]:
    return tuple(values[key] for values in TEXTS.values() if key in values)


def language_code_from_choice(text: str | None) -> str | None:
    return LANGUAGE_CHOICES.get((text or "").strip())
