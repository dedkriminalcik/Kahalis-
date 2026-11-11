from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.future import select
from database.models import async_session, User

router = Router()

def get_main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile"),
         InlineKeyboardButton(text="⛏ Работа", callback_data="work_menu")],
        [InlineKeyboardButton(text="🌌 Галактики & Рынок", callback_data="galaxy_menu"),
         InlineKeyboardButton(text="🚀 Космический Транспорт", callback_data="transport_menu")],
        [InlineKeyboardButton(text="💥 Рейды и Нападения", callback_data="raids_menu"),
         InlineKeyboardButton(text="🛡 Защита (Щиты)", callback_data="shields_menu")],
        [InlineKeyboardButton(text="🎁 Бонус", callback_data="daily_bonus"),
         InlineKeyboardButton(text="🎲 Ставки", callback_data="gambling_menu")]
    ])

@router.message(CommandStart())
async def cmd_start(message: Message):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == message.from_user.id))
        user = result.scalars().first()

        if not user:
            user = User(
                id=message.from_user.id,
                username=message.from_user.username or message.from_user.first_name
            )
            session.add(user)
            await session.commit()

    text = (
        f"🤖 Привет, **{message.from_user.first_name}**! Все модули бота активированы!\n\n"
        "🌌 **Космическая Империя — Обновление:**\n"
        "• Покупай галактики разного объема и цены, прокачивай и продавай их 📈.\n"
        "• Используй космический транспорт 🚀 для передвижения между секторами.\n"
        "• Совершай рейды на базы соперников и грабь часть их ресурсов 📦 (если пробьешь щиты).\n"
        "• Зарабатывай нейтрино (🪙), крути ставки и собирай бонусы!"
    )

    await message.answer(text, reply_markup=get_main_keyboard(), parse_mode="Markdown")

@router.callback_query(F.data == "back_main")
async def back_main(call: CallbackQuery):
    await call.message.edit_text("🛸 **Главное меню управления империей:**", reply_markup=get_main_keyboard(), parse_mode="Markdown")
