import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import ADMIN_IDS, BOT_TOKEN
from database.db import create_tables
from handlers.admin import router as admin_router
from handlers.dormitories import router as dorm_router
from handlers.history import router as history_router
from handlers.profile import router as profile_router
from handlers.registration import router as registration_router
from handlers.reservation import router as reservation_router
from handlers.start import router as start_router

storage = MemoryStorage()
dp = Dispatcher(storage=storage)

dp.include_router(start_router)
dp.include_router(profile_router)
dp.include_router(dorm_router)
dp.include_router(reservation_router)
dp.include_router(registration_router)
dp.include_router(history_router)
dp.include_router(admin_router)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))


async def on_startup(bot: Bot):
    admin_target = ADMIN_IDS[0] if ADMIN_IDS else None
    if admin_target:
        await bot.send_message(admin_target, "✅ Бот включен")


async def on_shutdown(bot: Bot):
    admin_target = ADMIN_IDS[0] if ADMIN_IDS else None
    if admin_target:
        await bot.send_message(admin_target, "❌ Бот выключен")


async def main():
    await create_tables()
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
