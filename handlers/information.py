from aiogram import F, Router
from aiogram.types import Message

from config import ADMIN_USERNAME, CONTACT_EMAIL, CONTACT_PHONE
from keyboards.user import CONTACTS_BUTTONS, INFO_BUTTONS

router = Router()


INFO_TEXT = """
ℹ️ <b>Інформація</b>

<b>Правила проживання</b>
• Дотримуйтесь тиші у нічний час.
• Підтримуйте чистоту в кімнаті та спільних зонах.
• Не пошкоджуйте майно гуртожитку.
• Про аварійні ситуації повідомляйте через розділ «Повідомити про проблему».

<b>Контакти адміністрації</b>
Адміністратор: {admin}
Email: {email}
Телефон: {phone}

<b>Години роботи</b>
Пн-Пт: 09:00-17:00
Сб-Нд: тільки термінові заявки

<b>Карта гуртожитків</b>
https://maps.google.com/?q=WSG+Bydgoszcz

<b>FAQ</b>
Питання: Хто має пріоритет на поселення?
Відповідь: Студенти WSG мають першу чергу.

Питання: Що буде, якщо місць немає?
Відповідь: Заявка автоматично потрапляє у список очікування.

Питання: Як дізнатися статус?
Відповідь: Відкрийте розділ «Мої заявки».
""".strip()


@router.message(F.text.in_(INFO_BUTTONS))
async def information(message: Message):
    await message.answer(
        INFO_TEXT.format(
            admin=ADMIN_USERNAME,
            email=CONTACT_EMAIL,
            phone=CONTACT_PHONE,
        )
    )


@router.message(F.text.in_(CONTACTS_BUTTONS))
async def contacts(message: Message):
    await message.answer(
        "📞 <b>Контакти</b>\n"
        f"Адміністратор: {ADMIN_USERNAME}\n"
        f"Email: {CONTACT_EMAIL}\n"
        f"Телефон: {CONTACT_PHONE}"
    )
