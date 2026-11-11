from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.future import select
from database.models import async_session, User, Galaxy

router = Router()

GALAXY_TYPES = {
    "spiral": {"name": "Спиральная Галактика", "price": 25000, "type": "Спиральная"},
    "elliptical": {"name": "Эллиптическая Галактика", "price": 75000, "type": "Эллиптическая"},
    "blackhole": {"name": "Галактика Черной Дыры", "price": 200000, "type": "Черная Дыра"},
    "quasar": {"name": "Кварковая Мега-Галактика", "price": 500000, "type": "Кварковая"}
}

@router.callback_query(F.data == "galaxy_menu")
async def galaxy_menu(call: CallbackQuery):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == call.from_user.id))
        user = result.scalars().first()

        if not user.own_galaxy_id:
            text = (
                "🌌 **РИНОК ГАЛАКТИК**\n\n"
                "Вы можете приобрести собственную галактику, собирать с нее налоги и строить империю!\n"
                "Выберите класс галактики для покупки:"
            )
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🌀 Спиральная (25,000 🪙)", callback_data="buy_gal_spiral")],
                [InlineKeyboardButton(text="🪐 Эллиптическая (75,000 🪙)", callback_data="buy_gal_elliptical")],
                [InlineKeyboardButton(text="🕳 Черная Дыра (200,000 🪙)", callback_data="buy_gal_blackhole")],
                [InlineKeyboardButton(text="✨ Кварковая (500,000 🪙)", callback_data="buy_gal_quasar")],
                [InlineKeyboardButton(text="◀️ В меню", callback_data="back_main")]
            ])
        else:
            g_res = await session.execute(select(Galaxy).where(Galaxy.id == user.own_galaxy_id))
            gal = g_res.scalars().first()

            text = (
                f"🌌 **ВАША ГАЛАКТИКА:** {gal.name}\n"
                f"🌟 **Класс:** {gal.galaxy_type}\n"
                f"🛡 **Уровень обороны сектора:** {gal.defense_level}\n"
                f"🪙 **Экономический потенциал:** {gal.economy_level}\n\n"
                "Ваша галактика полностью защищена от захвата! Другие игроки могут лишь пытаться грабить ресурсы, если пробьют ваши силовые щиты."
            )
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🛡 Улучшить щиты сектора (15,000 🪙)", callback_data="upgrade_g_def")],
                [InlineKeyboardButton(text="◀️ В меню", callback_data="back_main")]
            ])

        await call.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

@router.callback_query(F.data.startswith("buy_gal_"))
async def buy_galaxy_action(call: CallbackQuery):
    key = call.data.replace("buy_gal_", "")
    info = GALAXY_TYPES.get(key)

    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == call.from_user.id))
        user = result.scalars().first()

        if user.own_galaxy_id:
            await call.answer("У вас уже есть галактика!", show_alert=True)
            return

        if user.neutrinos < info["price"]:
            await call.answer("Недостаточно нейтрино (🪙)!", show_alert=True)
            return

        user.neutrinos -= info["price"]
        new_gal = Galaxy(
            name=f"Галактика {user.username}",
            galaxy_type=info["type"],
            owner_id=user.id
        )
        session.add(new_gal)
        await session.flush()

        user.own_galaxy_id = new_gal.id
        await session.commit()

        await call.answer(f"🎉 Поздравляем! Вы приобрели {info['name']}!", show_alert=True)
        await galaxy_menu(call)
