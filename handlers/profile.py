from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.future import select
from database.models import async_session, User, Galaxy

router = Router()

@router.callback_query(F.data == "profile")
async def show_profile(call: CallbackQuery):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == call.from_user.id))
        user = result.scalars().first()

        galaxy_name = "Нет (Общий сектор)"
        if user.own_galaxy_id:
            g_res = await session.execute(select(Galaxy).where(Galaxy.id == user.own_galaxy_id))
            gal = g_res.scalars().first()
            if gal:
                galaxy_name = f"{gal.name} ({gal.galaxy_type})"

        text = (
            f"👤 **ПРОФИЛЬ ПИЛОТА:** {user.username}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📈 **Уровень:** {user.level} (Опыт: {user.exp} / {user.level * 100})\n"
            f"🪙 **Нейтрино:** {user.neutrinos:,}\n"
            f"💎 **Квантиум:** {user.quantium}\n\n"
            f"🚀 **Корабль:** {user.ship_name}\n"
            f"⚔️ **Атака:** {user.attack} | 🛡 **Броня:** {user.defense}\n"
            f"💥 **Защитное поле (Слойка):** {user.shield_type} (Прочность: {user.shield_power})\n\n"
            f"🌌 **Личная Галактика:** {galaxy_name}"
        )

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ В главное меню", callback_data="back_main")]
        ])

        await call.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
