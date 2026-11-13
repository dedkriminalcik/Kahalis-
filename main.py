import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("8709941951:AAH7PwqO__uc59BCYKWzary6I_8CX4Pt3Uk")

logging.basicConfig(level=logging.INFO)

# Создаем постоянные кнопки снизу (ReplyKeyboardMarkup), как на твоем втором скриншоте
def get_bottom_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛠 Работа"), KeyboardButton(text="⛏ Шахта"), KeyboardButton(text="🎣 Рыбалка")],
            [KeyboardButton(text="🏡 Ранчо"), KeyboardButton(text="📦 Ящики"), KeyboardButton(text="💴 Бизнес")],
            [KeyboardButton(text="◀️ Меню")]
        ],
        resize_keyboard=True  # Делает кнопки аккуратными и компактными
    )

async def main():
    if not TOKEN:
        print("❌ Ошибка: BOT_TOKEN не найден!")
        return

    bot = Bot(token=TOKEN)
    dp = Dispatcher()

    # Обработчик команды /start — сразу запускает бота без всяких подписок
    @dp.message(F.text == "/start")
    async def cmd_start(message: Message):
        text = (
            f"🛸 Привет, **{message.from_user.first_name}**!\n\n"
            "Добро пожаловать в космическую империю! Все системы запущены. "
            "Используй кнопки внизу экрана для управления:"
        )
        await message.answer(text, reply_markup=get_bottom_keyboard(), parse_mode="Markdown")

    # Обработчики нажатий на нижние кнопки
    @dp.message(F.text == "🛠 Работа")
    async def work_handler(message: Message):
        await message.answer("🪙 Вы отправились на смену в Общий Сектор и заработали +300 кредитов!", reply_markup=get_bottom_keyboard())

    @dp.message(F.text == "⛏ Шахта")
    async def mine_handler(message: Message):
        await message.answer("💎 Вы спустились в астероидную шахту и добыли редкие ресурсы!", reply_markup=get_bottom_keyboard())

    @dp.message(F.text == "🎣 Рыбалка")
    async def fish_handler(message: Message):
        await message.answer("🌌 Закинули квантовый гарпун в открытый космос и поймали космического улова!", reply_markup=get_bottom_keyboard())

    @dp.message(F.text == "📦 Ящики")
    async def boxes_handler(message: Message):
        await message.answer("📦 Вы открыли грузовой контейнер и нашли ценный лут!", reply_markup=get_bottom_keyboard())

    @dp.message(F.text.in_(["🏡 Ранчо", "💴 Бизнес", "◀️ Меню"]))
    async def general_menu_handler(message: Message):
        await message.answer(f"📁 Раздел «{message.text}» открыт и готов к работе!", reply_markup=get_bottom_keyboard())

    print("🚀 Бот успешно запущен без проверок подписок!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен.")
