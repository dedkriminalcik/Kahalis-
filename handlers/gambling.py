import random
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.future import select
from database.models import async_session, User

router = Router()

@router.callback_query(F.data == "gambling_menu")
async def gambling_menu(call: CallbackQuery):
    text = (
        "🎲 **КОСМИЧЕСКОЕ КАЗИНО (СТАВКИ)**\n\n"
        "Испытайте удачу! Сделайте ставку на квантовый генератор чисел. Если выпадет число больше 4 — вы побеждаете и удваиваете ставку!"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎲 Поставить 500 🪙", callback_data="bet_500"),
         InlineKeyboardButton(text="🎲 Поставить 2,000 🪙", callback_data="bet_2000")],
        [InlineKeyboardButton(text="🎲 Поставить 10,000 🪙", callback_data="bet_10000")],
        [InlineKeyboardButton(text="◀️ В меню", callback_data="back_main")]
    ])
    await call.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

@router.callback_query(F.data.startswith("bet_"))
async def play_bet(call: CallbackQuery):
    amount = int(call.data.replace("bet_", ""))

    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == call.from_user.id))
        user = result.scalars().first()

        if user.neutrinos < amount:
            await call.answer("Недостаточно нейтрино для ставки!", show_alert=True)
            return

        dice = random.randint(1, 6)
        if dice >= 4:
            win_amount = amount * 2
            user.neutrinos += amount  # чистый выигрыш
            res_text = f"🎉 **ПОБЕДА!** Выпало число: **{dice}**.\nВы выиграли **+{win_amount:,} нейтрино (🪙)**!"
        else:
            user.neutrinos -= amount
            res_text = f"😢 **ПРОИГРЫШ...** Выпало число: **{dice}**.\nВы потеряли ставку: **-{amount:,} нейтрино**."

        await session.commit()

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎲 Сыграть еще", callback_data="gambling_menu")],
            [InlineKeyboardButton(text="◀️ В меню", callback_data="back_main")]
        ])

        await call.message.edit_text(res_text, reply_markup=kb, parse_mode="Markdown")
