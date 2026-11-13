import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

# ⚠️ Впиши сюда свой реальный Telegram ID цифрами (узнать у @userinfobot)
OWNER_ID = 123456789  

logging.basicConfig(level=logging.INFO)

# 🌐 ВСТАВЬ СЮДА СВОЮ ССЫЛКУ НА GITHUB PAGES (например: https://твой_логин.github.io/репозиторий/)
WEBAPP_URL = "https://t.me/your_webapp_link" 

def get_main_menu(is_owner: bool = False):
    keyboard = [
        [InlineKeyboardButton(text="🚀 Запустить KAHALIS RPG", web_app=WebAppInfo(url=WEBAPP_URL))],
        [InlineKeyboardButton(text="🛠 Работа в секторе", callback_data="menu_work"),
         InlineKeyboardButton(text="👤 Профиль пилота", callback_data="menu_profile")]
    ]
    if is_owner:
        keyboard.insert(0, [InlineKeyboardButton(text="⚙️ Консоль владельца", callback_data="owner_console")])
        
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

async def main():
    if not TOKEN:
        print("❌ Ошибка: BOT_TOKEN не найден!")
        return

    bot = Bot(token=TOKEN)
    dp = Dispatcher()

    @dp.message(F.text == "/start")
    async def cmd_start(message: Message):
        is_owner = (message.from_user.id == OWNER_ID)
        await message.answer(
            "🌌 **Космический терминал KAHALIS:**\n\n"
            "Добро пожаловать в сектор! Все системы управления, кланы, бои и прокачка перенесены в полноценный Web App интерфейс.\n\n"
            "Нажми кнопку ниже, чтобы запустить приложение:",
            reply_markup=get_main_menu(is_owner),
            parse_mode="Markdown"
        )

    @dp.callback_query(F.data == "owner_console")
    async def owner_console(call: CallbackQuery):
        if call.from_user.id != OWNER_ID:
            await call.answer("⛔ Недостаточно прав!", show_alert=True)
            return
        await call.message.edit_text(
            "⚙️ **Консоль владельца:**\nСервер работает в штатном режиме.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Назад", callback_data="menu_main")]
            ]),
            parse_mode="Markdown"
        )
        await call.answer()

    @dp.callback_query(F.data == "menu_main")
    async def back_to_main(call: CallbackQuery):
        is_owner = (call.from_user.id == OWNER_ID)
        await call.message.edit_text(
            "🌌 **Космический терминал KAHALIS:**",
            reply_markup=get_main_menu(is_owner),
            parse_mode="Markdown"
        )
        await call.answer()

    @dp.callback_query(F.data == "menu_work")
    async def open_work(call: CallbackQuery):
        await call.message.edit_text(
            "🛠 Открой Mini App для полноценной работы в шахте и боев!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🚀 Запустить Mini App", web_app=WebAppInfo(url=WEBAPP_URL))],
                [InlineKeyboardButton(text="◀️ Назад", callback_data="menu_main")]
            ]),
            parse_mode="Markdown"
        )
        await call.answer()

    @dp.callback_query(F.data == "menu_profile")
    async def profile(call: CallbackQuery):
        await call.message.edit_text(
            f"👤 Ваш Telegram ID: `{call.from_user.id}`\nОткройте Mini App для детальной статистики.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🚀 Запустить Mini App", web_app=WebAppInfo(url=WEBAPP_URL))],
                [InlineKeyboardButton(text="◀️ Назад", callback_data="menu_main")]
            ]),
            parse_mode="Markdown"
        )
        await call.answer()

    print("🚀 Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
