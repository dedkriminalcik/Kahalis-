from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

router = Router()

# Динамическая генерация кнопок в зависимости от статуса игрока
def get_dynamic_keyboard(level: int):
    buttons = [
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile"),
         InlineKeyboardButton(text="⛏ Работать", callback_data="work")]
    ]
    
    # Если уровень игрока выше 5, открывается секретный сектор
    if level >= 5:
        buttons.append([InlineKeyboardButton(text="🌌 Секретный Сектор ✨", callback_data="secret_galaxy")])
        
    buttons.append([InlineKeyboardButton(text="🔄 Обновить меню", callback_data="refresh_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@router.message(F.text == "/start")
async def cmd_start(message: Message):
    # Допустим, уровень игрока равен 3 (для примера)
    player_level = 3
    
    text = (
        f"🛸 **Космический терминал активен!**\n"
        f"Ваш текущий уровень: {level_text := player_level}\n\n"
        "Выберите действие на панели управления:"
    )
    await message.answer(text, reply_markup=get_dynamic_keyboard(player_level), parse_mode="Markdown")

@router.callback_query(F.data == "refresh_menu")
async def refresh_menu(call: CallbackQuery):
    # Пример изменения кнопок «на лету» при обновлении
    await call.message.edit_text(
        "🔄 Меню успешно обновлено актуальными данными из базы!",
        reply_markup=get_dynamic_keyboard(level=5), # Меняем уровень, чтобы показать появление новой кнопки
        parse_mode="Markdown"
    )
    await call.answer("Данные синхронизированы!")
