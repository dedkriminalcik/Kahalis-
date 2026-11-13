import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("8709941951:AAEWBX1IQJZoikAgEYh8trfT0xtKGo7-0KU")

logging.basicConfig(level=logging.INFO)

# 1. Главное меню
def get_main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛠 Работа", callback_data="menu_work"),
         InlineKeyboardButton(text="👤 Профиль", callback_data="menu_profile")]
    ])

# 2. Меню заданий (появляется при нажатии на «Работа»)
def get_work_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⛏ Шахта", callback_data="task_mine"),
         InlineKeyboardButton(text="🎣 Рыбалка", callback_data="task_fish")],
        [InlineKeyboardButton(text="◀️ Назад в меню", callback_data="menu_main")]
    ])

# 3. Кнопка возврата назад к списку работ
def get_back_to_work():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад к работе", callback_data="menu_work")]
    ])

async def main():
    if not TOKEN:
        print("❌ Ошибка: BOT_TOKEN не найден!")
        return

    bot = Bot(token=TOKEN)
    dp = Dispatcher()

    @dp.message(F.text == "/start")
    async def cmd_start(message: Message):
        await message.answer(
            "🌌 **Космический терминал управления:**\nВыберите нужный раздел:",
            reply_markup=get_main_menu(),
            parse_mode="Markdown"
        )

    @dp.callback_query(F.data == "menu_main")
    async def back_to_main(call: CallbackQuery):
        await call.message.edit_text(
            "🌌 **Космический терминал управления:**\nВыберите нужный раздел:",
            reply_markup=get_main_menu(),
            parse_mode="Markdown"
        )
        await call.answer()

    @dp.callback_query(F.data == "menu_work")
    async def open_work(call: CallbackQuery):
        await call.message.edit_text(
            "🛠 **Выберите задание для смены:**",
            reply_markup=get_work_menu(),
            parse_mode="Markdown"
        )
        await call.answer()

    @dp.callback_query(F.data == "task_mine")
    async def task_mine(call: CallbackQuery):
        await call.message.edit_text(
            "⛏ Вы спустились в астероидную шахту и добыли **150 редких кристаллов**! 💎",
            reply_markup=get_back_to_work(),
            parse_mode="Markdown"
        )
        await call.answer("Задание успешно выполнено!")

    @dp.callback_query(F.data == "task_fish")
    async def task_fish(call: CallbackQuery):
        await call.message.edit_text(
            "🎣 Вы закинули квантовый гарпун и поймали **космического левиафана**! 🐋",
            reply_markup=get_back_to_work(),
            parse_mode="Markdown"
        )
        await call.answer("Улов успешно записан в трюм!")

    @dp.callback_query(F.data == "menu_profile")
    async def profile(call: CallbackQuery):
        await call.message.edit_text(
            "👤 **Ваш профиль пилота:**\n\n🔹 Уровень: 3\n🔹 Баланс: 2,400 кредитов 🪙",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Назад", callback_data="menu_main")]
            ]),
            parse_mode="Markdown"
        )
        await call.answer()

    print("🚀 Бот успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
