import datetime
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.future import select
from database.models import async_session, User

router = Router()

@router.callback_query(F.data == "daily_bonus")
async def daily_bonus(call: CallbackQuery):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == call.from_user.id))
        user = result.scalars().first()

        now = datetime.datetime.utcnow()
        if user.last_bonus_time:
            time_diff = now - user.last_bonus_time
            if time_diff < datetime.timedelta(hours=24):
                hours_left = 23 - int(time_diff.total_seconds() // 3600)
                await call.answer(f"⏳ Бонус уже получен! Следующий будет через {hours_left} ч.", show_alert=True)
                return

        bonus_neutrinos = 2000 * user.level
        bonus_quantium = 5

        user.neutrinos += bonus_neutrinos
        user.quantium += bonus_quantium
        user.last_bonus_time = now
        await session.commit()

        text = (
            f"🎁 **ЕЖЕДНЕВНЫЙ БОНУС ПОЛУЧЕН!**\n\n"
            f"🪙 Нейтрино: **+{bonus_neutrinos:,}**\n"
            f"💎 Квантиум: **+{bonus_quantium}**\n\n"
            "Возвращайтесь завтра за новой наградой!"
        )

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ В меню", callback_data="back_main")]
        ])

        await call.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
