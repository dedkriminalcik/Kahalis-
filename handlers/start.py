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
        [InlineKeyboardButton(text="🌌 Галактики", callback_data="galaxy_menu"),
         InlineKeyboardButton(text="🛡 Защита (Щиты)", callback_data="shields_menu")],
        [InlineKeyboardButton(text="🎁 Ежедневный бонус", callback_data="daily_bonus"),
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
        f"🤖 Привет, **{message.from_user.first_name}**! Бот активен и готов к работе!\n\n"
        "🌌 Добро пожаловать в масштабную космическую RPG!\n"
        "• Зарабатывай **нейтрино (🪙)** на разных работах.\n"
        "• Покупай уникальные **Галактики** и строй экономику.\n"
        "• Приобретай **защитные поля (слойки)**, чтобы полностью отражать урон соперников 💥.\n"
        "• Испытывай удачу в ставках и забирай ежедневные бонусы!"
    )

    await message.answer(text, reply_markup=get_main_keyboard(), parse_mode="Markdown")

@router.callback_query(F.data == "back_main")
async def back_main(call: CallbackQuery):
    await call.message.edit_text("🛸 **Главное меню управления империей:**", reply_markup=get_main_keyboard(), parse_mode="Markdown")
