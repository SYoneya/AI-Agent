from aiogram import F, Router
from aiogram.types import Message

from config import ADMIN_USERNAME, CONTACT_EMAIL, CONTACT_PHONE
from database.db import get_user_by_telegram_id
from keyboards.user import CONTACTS_BUTTONS, INFO_BUTTONS
from locales import language_from_user

router = Router()


INFO_TEXTS = {
    "uk": """
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
""".strip(),
    "en": """
ℹ️ <b>Information</b>

<b>Residence rules</b>
• Keep quiet at night.
• Keep your room and shared areas clean.
• Do not damage dormitory property.
• Report urgent situations via “Report a problem”.

<b>Administration contacts</b>
Administrator: {admin}
Email: {email}
Phone: {phone}

<b>Working hours</b>
Mon-Fri: 09:00-17:00
Sat-Sun: urgent requests only

<b>Dormitory map</b>
https://maps.google.com/?q=WSG+Bydgoszcz

<b>FAQ</b>
Question: Who has priority for accommodation?
Answer: WSG students have first priority.

Question: What if there are no places?
Answer: The request automatically goes to the waiting list.
""".strip(),
    "pl": """
ℹ️ <b>Informacje</b>

<b>Zasady mieszkania</b>
• Zachowuj ciszę nocną.
• Dbaj o czystość w pokoju i częściach wspólnych.
• Nie niszcz mienia akademika.
• Sytuacje awaryjne zgłaszaj przez „Zgłoś problem”.

<b>Kontakt z administracją</b>
Administrator: {admin}
Email: {email}
Telefon: {phone}

<b>Godziny pracy</b>
Pn-Pt: 09:00-17:00
Sb-Nd: tylko pilne zgłoszenia

<b>Mapa akademików</b>
https://maps.google.com/?q=WSG+Bydgoszcz

<b>FAQ</b>
Pytanie: Kto ma pierwszeństwo zakwaterowania?
Odpowiedź: Studenci WSG mają pierwszeństwo.

Pytanie: Co jeśli nie ma miejsc?
Odpowiedź: Zgłoszenie automatycznie trafia na listę oczekujących.
""".strip(),
}

CONTACT_TEXTS = {
    "uk": "📞 <b>Контакти</b>\nАдміністратор: {admin}\nEmail: {email}\nТелефон: {phone}",
    "en": "📞 <b>Contacts</b>\nAdministrator: {admin}\nEmail: {email}\nPhone: {phone}",
    "pl": "📞 <b>Kontakty</b>\nAdministrator: {admin}\nEmail: {email}\nTelefon: {phone}",
}


async def get_language(message: Message) -> str:
    user = await get_user_by_telegram_id(message.from_user.id)
    return language_from_user(user)


def format_text(template: str) -> str:
    return template.format(
        admin=ADMIN_USERNAME,
        email=CONTACT_EMAIL,
        phone=CONTACT_PHONE,
    )


@router.message(F.text.in_(INFO_BUTTONS))
async def information(message: Message):
    language = await get_language(message)
    await message.answer(format_text(INFO_TEXTS.get(language, INFO_TEXTS["uk"])))


@router.message(F.text.in_(CONTACTS_BUTTONS))
async def contacts(message: Message):
    language = await get_language(message)
    await message.answer(format_text(CONTACT_TEXTS.get(language, CONTACT_TEXTS["uk"])))
