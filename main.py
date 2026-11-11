import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

from database.models import init_db
from handlers import start, profile, work, galaxy, clan

load_dotenv()
TOKEN = os.getenv("8709941951:AAH7PwqO__uc59BCYKWzary6I_8CX4Pt3Uk")

async def main():
    logging.basicConfig(level=logging.INFO)
    
    if not TOKEN:
        print("Ошибка: BOT_TOKEN не найден в файле .env!")
        return

    # Инициализация БД (создание всех таблиц при запуске)
    await init_db()

    bot = Bot(token=TOKEN)
    dp = Dispatcher()

    # Регистрация всех модулей бота
    dp.include_router(start.router)
    dp.include_router(profile.router)
    dp.include_router(work.router)
    dp.include_router(galaxy.router)
    dp.include_router(clan.router)

    print("🚀 Космический RPG бот успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен.")
