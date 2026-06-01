from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

ADMIN_IDS = [
    int(x)
    for x in os.getenv("ADMIN_IDS", "").split(",")
    if x.strip()
]

# Fallback admin and contact details (will be used if ENV vars are not set)
if not ADMIN_IDS:
    ADMIN_IDS = [8605127546]

CONTACT_EMAIL = os.getenv("CONTACT_EMAIL", "yoneyadev@gmail.com")
CONTACT_PHONE = os.getenv("CONTACT_PHONE", "+48507360391")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "@Sekai_Yoneya")