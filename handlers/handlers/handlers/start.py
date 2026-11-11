from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    # Кнопки главного меню игры
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile"),
         InlineKeyboardButton(text="⚔️ В бой / Квесты", callback_data="adventure")],
        [InlineKeyboardButton(text="🎒 Инвентарь", callback_data="inventory"),
         InlineKeyboardButton(text="🛒 Магазин", callback_data="shop")]
    ])
    
    user_name = message.from_user.first_name
    text = (
        f"Привет, **{user_name}**! Добро пожаловать в мир текстовой RPG.\n\n"
        "Выбери действие в меню ниже, чтобы начать свое приключение, прокачивать "
        "персонажа и сражаться с монстрами."
    )
    
    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
