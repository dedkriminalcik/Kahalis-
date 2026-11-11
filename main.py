import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)

# Динамическая генерация кнопок
def get_dynamic_keyboard(level: int):
    buttons = [
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile"),
         InlineKeyboardButton(text="⛏ Работать", callback_data="work")]
    ]
    
    # Если уровень выше 5, добавляется секретный сектор
    if level >= 5:
        buttons.append([InlineKeyboardButton(text="🌌 Секретный Сектор ✨", callback_data="secret_galaxy")])
        
    buttons.append([InlineKeyboardButton(text="🔄 Обновить меню", callback_data="refresh_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

async def main():
    if not TOKEN:
        print("❌ Ошибка: BOT_TOKEN не найден в переменных окружения Railway!")
        return

    bot = Bot(token=TOKEN)
    dp = Dispatcher()

    # Обработчик команды /start
    @dp.message(F.text == "/start")
    async def cmd_start(message: Message):
        player_level = 3  # Для примера
        text = (
            f"🛸 **Космический терминал активен!**\n"
            f"Ваш текущий уровень: {player_level}\n\n"
            "Выберите действие на панели управления:"
        )
        await message.answer(text, reply_markup=get_dynamic_keyboard(player_level), parse_mode="Markdown")

    # Обработчик кнопки обновления меню
    @dp.callback_query(F.data == "refresh_menu")
    async def refresh_menu(call: CallbackQuery):
        await call.message.edit_text(
            "🔄 Меню успешно обновлено актуальными данными из базы!",
            reply_markup=get_dynamic_keyboard(level=5),
            parse_mode="Markdown"
        )
        await call.answer("Данные синхронизированы!")

    # Обработчик профиля
    @dp.callback_query(F.data == "profile")
    async def profile_cb(call: CallbackQuery):
        await call.answer("Загрузка профиля...")
        await call.message.answer("👤 Ваш профиль пилота успешно открыт.")

    print("🚀 Бот успешно запущен и слушает Telegram API!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен.")
