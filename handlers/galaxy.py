from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.future import select
from database.models import async_session, User, Galaxy

router = Router()
GALAXY_PRICE = 50000

@router.callback_query(F.data == "my_galaxy")
async def my_galaxy(call: CallbackQuery):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == call.from_user.id))
        user = result.scalars().first()

        if not user.own_galaxy_id:
            text = (
                "🌌 **У вас пока нет собственной Галактики.**\n\n"
                "Вы находитесь в Общем Секторе. Покупка личной галактики дает возможность:\n"
                "• Строить планетные системы и щиты\n"
                "• Собирать налоги с прилетающих игроков\n"
                "• Защищать свои богатства от набегов врагов!\n\n"
                f"💰 **Стоимость лицензии Галактики:** {GALAXY_PRICE:,} кредитов."
            )
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=f"💳 Купить Галактику ({GALAXY_PRICE:,})", callback_data="buy_galaxy")],
                [InlineKeyboardButton(text="◀️ В меню", callback_data="back_main")]
            ])
        else:
            g_res = await session.execute(select(Galaxy).where(Galaxy.id == user.own_galaxy_id))
            gal = g_res.scalars().first()

            text = (
                f"🌌 **ГАЛАКТИКА:** {gal.name}\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"🛡 **Уровень обороны / Щитов:** {gal.defense_level}\n"
                f"🏗 **Уровень экономики:** {gal.economy_level}\n\n"
                "Ваша галактика защищена от полной потери! Враги могут лишить вас лишь части наворованных ресурсов при пробое щитов."
            )
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🛡 Улучшить Щиты (10,000)", callback_data="upgrade_defense")],
                [InlineKeyboardButton(text="🏗 Улучшить Экономику (10,000)", callback_data="upgrade_economy")],
                [InlineKeyboardButton(text="◀️ В меню", callback_data="back_main")]
            ])

        await call.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

@router.callback_query(F.data == "buy_galaxy")
async def buy_galaxy(call: CallbackQuery):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == call.from_user.id))
        user = result.scalars().first()

        if user.own_galaxy_id:
            await call.answer("У вас уже есть галактика!", show_alert=True)
            return

        if user.credits < GALAXY_PRICE:
            await call.answer("Недостаточно кредитов!", show_alert=True)
            return

        user.credits -= GALAXY_PRICE
        new_galaxy = Galaxy(name=f"Сектор {user.username}", owner_id=user.id)
        session.add(new_galaxy)
        await session.flush()

        user.own_galaxy_id = new_galaxy.id
        await session.commit()

        await call.answer("🎉 Поздравляем! Вы приобрели собственную Галактику!", show_alert=True)
        await my_galaxy(call)
