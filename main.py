import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, LabeledPrice, PreCheckoutQuery
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = 6188701923

logging.basicConfig(level=logging.INFO)
WEBAPP_URL = "https://твой_логин.github.io/твой_репозиторий/"  # Замени на свою ссылку GitHub Pages

async def main():
    if not TOKEN:
        print("❌ Ошибка: BOT_TOKEN не найден!")
        return

    bot = Bot(token=TOKEN)
    dp = Dispatcher()

    @dp.message(F.text == "/start")
    async def cmd_start(message: Message):
        is_owner = (message.from_user.id == OWNER_ID)
        keyboard = [
            [InlineKeyboardButton(text="🚀 Запустить KAHALIS RPG", web_app=WebAppInfo(url=WEBAPP_URL))],
            [InlineKeyboardButton(text="⭐ Купить кредиты за Telegram Stars", callback_data="buy_stars_menu")]
        ]
        if is_owner:
            keyboard.insert(0, [InlineKeyboardButton(text="⚙️ Консоль владельца", callback_data="owner_console")])

        await message.answer(
            "🌌 **Космический терминал KAHALIS:**\n\n"
            "Добро пожаловать в сектор! Выберите действие:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
            parse_mode="Markdown"
        )

    @dp.callback_query(F.data == "buy_stars_menu")
    async def stars_menu(call: CallbackQuery):
        await call.message.edit_text(
            "⭐ **Магазин Telegram Stars:**\nВыберите пакет для покупки за звезды:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⭐ 100 Stars (= 5,000 🪙)", callback_data="pay_star_100")],
                [InlineKeyboardButton(text="⭐ 500 Stars (= 30,000 🪙)", callback_data="pay_star_500")],
                [InlineKeyboardButton(text="◀️ Назад", callback_data="menu_main")]
            ]),
            parse_mode="Markdown"
        )
        await call.answer()

    @dp.callback_query(F.data == "pay_star_100")
    async def pay_100(call: CallbackQuery):
        prices = [LabeledPrice(label="100 Telegram Stars", amount=100)]
        await call.message.answer_invoice(
            title="Пакет кредитов [100 Stars]",
            description="Дает 5,000 кредитов 🪙 на баланс в KAHALIS RPG.",
            prices=prices,
            provider_token="",
            payload="stars_100_pack",
            currency="XTR",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⭐ Оплатить 100 Stars", pay=True)],
                [InlineKeyboardButton(text="◀️ Назад", callback_data="buy_stars_menu")]
            ])
        )
        await call.answer()

    @dp.callback_query(F.data == "pay_star_500")
    async def pay_500(call: CallbackQuery):
        prices = [LabeledPrice(label="500 Telegram Stars", amount=500)]
        await call.message.answer_invoice(
            title="Пакет кредитов [500 Stars]",
            description="Дает 30,000 кредитов 🪙 на баланс в KAHALIS RPG.",
            prices=prices,
            provider_token="",
            payload="stars_500_pack",
            currency="XTR",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⭐ Оплатить 500 Stars", pay=True)],
                [InlineKeyboardButton(text="◀️ Назад", callback_data="buy_stars_menu")]
            ])
        )
        await call.answer()

    @dp.pre_checkout_query()
    async def pre_checkout(pre_checkout_query: PreCheckoutQuery):
        await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

    @dp.message(F.successful_payment)
    async def successful_payment(message: Message):
        payment_info = message.successful_payment
        reward = 5000 if payment_info.invoice_payload == "stars_100_pack" else 30000
        await message.answer(f"🎉 **Оплата прошла успешно!**\nВам начислено +{reward} 🪙. Зайдите в Mini App!", parse_mode="Markdown")

    @dp.callback_query(F.data == "menu_main")
    async def back_to_main(call: CallbackQuery):
        is_owner = (call.from_user.id == OWNER_ID)
        keyboard = [
            [InlineKeyboardButton(text="🚀 Запустить KAHALIS RPG", web_app=WebAppInfo(url=WEBAPP_URL))],
            [InlineKeyboardButton(text="⭐ Купить кредиты за Telegram Stars", callback_data="buy_stars_menu")]
        ]
        if is_owner:
            keyboard.insert(0, [InlineKeyboardButton(text="⚙️ Консоль владельца", callback_data="owner_console")])
        await call.message.edit_text("🌌 **Космический терминал KAHALIS:**", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="Markdown")

    print("🚀 Бот запущен со звёздами!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
