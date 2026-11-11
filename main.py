import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()
TOKEN = os.getenv("8709941951:AAH7PwqO__uc59BCYKWzary6I_8CX4Pt3Uk")

async def main():
    logging.basicConfig(level=logging.INFO)
    
    if not TOKEN:
        print("Ошибка: Не найден BOT_TOKEN в файле .env")
        return

    bot = Bot(token=TOKEN)
    dp = Dispatcher()

    # Здесь будут подключаться роутеры (handlers)
    # dp.include_router(start.router)
    # dp.include_router(profile.router)

    print("Бот запущен и готов к работе...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен.")
