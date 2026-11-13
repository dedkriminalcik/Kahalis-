import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from dotenv import load_dotenv

load_dotenv()

# Токен автоматически подтягивается из защищенных переменных Railway
TOKEN = os.getenv("BOT_TOKEN")

# ⚠️ Впиши сюда свой реальный Telegram ID цифрами (узнать можно у @userinfobot), чтобы получить доступ к консоли владельца
OWNER_ID = 123456789  

logging.basicConfig(level=logging.INFO)

# Ссылка на твой Mini App (замени на свою ссылку GitHub Pages или оставь заглушку)
WEBAPP_URL = "https://github.com" 

# Главное меню пилота
def get_main_menu(is_owner: bool = False):
    keyboard = [
        [InlineKeyboardButton(text="🚀 Запустить Mini App", web_app=WebAppInfo(url=WEBAPP_URL))],
        [InlineKeyboardButton(text="🛠 Работа", callback_data="menu_work"),
         InlineKeyboardButton(text="👤 Профиль", callback_data="menu_profile")]
    ]
    if is_owner:
        keyboard.insert(0, [InlineKeyboardButton(text="⚙️ Консоль владельца", callback_data="owner_console")])
        
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_work_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⛏ Шахта", callback_data="task_mine"),
         InlineKeyboardButton(text="🎣 Рыбалка", callback_data="task_fish")],
        [InlineKeyboardButton(text="◀️ Назад в меню", callback_data="menu_main")]
    ])

def get_back_to_work():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад к работе", callback_data="menu_work")]
    ])

async def main():
    if not TOKEN:
        print("❌ Ошибка: BOT_TOKEN не найден в переменных окружения!")
        return

    bot = Bot(token=TOKEN)
    dp = Dispatcher()

    @dp.message(F.text == "/start")
    async def cmd_start(message: Message):
        is_owner = (message.from_user.id == OWNER_ID)
        await message.answer(
            "🌌 **Космический терминал управления:**\n"
            "Добро пожаловать в сектор! Выберите действие или откройте Mini App:",
            reply_markup=get_main_menu(is_owner),
            parse_mode="Markdown"
        )

    @dp.callback_query(F.data == "owner_console")
    async def owner_console(call: CallbackQuery):
        if call.from_user.id != OWNER_ID:
            await call.answer("⛔ У вас нет доступа к этой панели!", show_alert=True)
            return
            
        await call.message.edit_text(
            "⚙️ **Панель управления владельца (Консоль):**\n\n"
            "• Статус ядра: Активно\n"
            "• База данных: Подключена\n"
            "• Управление экономикой и ролями:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📊 Статистика", callback_data="stat_servers")],
                [InlineKeyboardButton(text="◀️ Назад", callback_data="menu_main")]
            ]),
            parse_mode="Markdown"
        )
        await call.answer()

    @dp.callback_query(F.data == "menu_main")
    async def back_to_main(call: CallbackQuery):
        is_owner = (call.from_user.id == OWNER_ID)
        await call.message.edit_text(
            "🌌 **Космический терминал управления:**\nВыберите нужный раздел:",
            reply_markup=get_main_menu(is_owner),
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
