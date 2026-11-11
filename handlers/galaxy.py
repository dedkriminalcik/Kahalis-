from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.future import select
from database.models import async_session, User, Galaxy

router = Router()

GALAXY_STORE = {
    "g1": {"name": "Малая Спираль", "vol": "Малый (10 планет)", "price": 25000, "type": "Спиральная"},
    "g2": {"name": "Эллипс Процион", "vol": "Средний (50 планет)", "price": 85000, "type": "Эллиптическая"},
    "g3": {"name": "Мега-Кластер Андромеды", "vol": "Огромный (250 планет)", "price": 250000, "type": "Кластерная"},
    "g4": {"name": "Империя Квазар", "vol": "Безграничный (Вселенная)", "price": 750000, "type": "Кварковая"}
}

@router.callback_query(F.data == "galaxy_menu")
async def galaxy_menu(call: CallbackQuery):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == call.from_user.id))
        user = result.scalars().first()

        if not user.own_galaxy_id:
            text = (
                "🌌 **МЕЖГАЛАКТИЧЕСКАЯ БИРЖА**\n\n"
                "Галактики имеют разный объем, класс и цену 💰. Вы можете купить одну, прокачать её инфраструктуру и выгодно продать 📈!\n\n"
                "Выберите галактику для покупки:"
            )
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🌀 Малая Спираль (25,000 🪙)", callback_data="buy_g_g1")],
                [InlineKeyboardButton(text="🪐 Эллипс Процион (85,000 🪙)", callback_data="buy_g_g2")],
                [InlineKeyboardButton(text="✨ Кластер Андромеды (250,000 🪙)", callback_data="buy_g_g3")],
                [InlineKeyboardButton(text="💥 Империя Квазар (750,000 🪙)", callback_data="buy_g_g4")],
                [InlineKeyboardButton(text="◀️ В меню", callback_data="back_main")]
            ])
        else:
            g_res = await session.execute(select(Galaxy).where(Galaxy.id == user.own_galaxy_id))
            gal = g_res.scalars().first()

            sell_price = int(gal.price * (1 + (gal.upgrade_stage * 0.25)))

            text = (
                f"🌌 **ВАША ГАЛАКТИКА:** {gal.name}\n"
                f"📦 Объем: {gal.volume_class}\n"
                f"📈 Уровень прокачки: {gal.upgrade_stage} стадия\n"
                f"🛡 Оборона сектора: {gal.defense_level}\n\n"
                f"💵 Рыночная стоимость при продаже: **{sell_price:,} 🪙**"
            )
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📈 Прокачать галактику (20,000 🪙)", callback_data="upgrade_galaxy_tier")],
                [InlineKeyboardButton(text=f"💵 Продать галактику за {sell_price:,}", callback_data="sell_galaxy")],
                [InlineKeyboardButton(text="◀️ В меню", callback_data="back_main")]
            ])

        await call.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

@router.callback_query(F.data.startswith("buy_g_"))
async def buy_galaxy_shop(call: CallbackQuery):
    key = call.data.replace("buy_g_", "")
    info = GALAXY_STORE.get(key)

    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == call.from_user.id))
        user = result.scalars().first()

        if user.own_galaxy_id:
            await call.answer("У вас уже есть галактика! Сначала продайте текущую.", show_alert=True)
            return

        if user.neutrinos < info["price"]:
            await call.answer("Недостаточно нейтрино (🪙)!", show_alert=True)
            return

        user.neutrinos -= info["price"]
        new_gal = Galaxy(
            name=f"Галактика {user.username}",
            galaxy_type=info["type"],
            volume_class=info["vol"],
            price=info["price"],
            owner_id=user.id
        )
        session.add(new_gal)
        await session.flush()

        user.own_galaxy_id = new_gal.id
        await session.commit()

        await call.answer(f"🎉 Вы успешно приобрели {info['name']}!", show_alert=True)
        await galaxy_menu(call)

@router.callback_query(F.data == "upgrade_galaxy_tier")
async def upgrade_galaxy_tier(call: CallbackQuery):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == call.from_user.id))
        user = result.scalars().first()

        if not user.own_galaxy_id:
            return

        g_res = await session.execute(select(Galaxy).where(Galaxy.id == user.own_galaxy_id))
        gal = g_res.scalars().first()

        cost = 20000 * gal.upgrade_stage
        if user.neutrinos < cost:
            await call.answer(f"Нужно {cost:,} 🪙 для прокачки галактики!", show_alert=True)
            return

        user.neutrinos -= cost
        gal.upgrade_stage += 1
        gal.defense_level += 2
        await session.commit()

        await call.answer(f"📈 Галактика улучшена до {gal.upgrade_stage} уровня!", show_alert=True)
        await galaxy_menu(call)

@router.callback_query(F.data == "sell_galaxy")
async def sell_galaxy(call: CallbackQuery):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == call.from_user.id))
        user = result.scalars().first()

        if not user.own_galaxy_id:
            return

        g_res = await session.execute(select(Galaxy).where(Galaxy.id == user.own_galaxy_id))
        gal = g_res.scalars().first()

        refund = int(gal.price * (1 + (gal.upgrade_stage * 0.25)))
        user.neutrinos += refund
        user.own_galaxy_id = None
        
        await session.delete(gal)
        await session.commit()

        await call.answer(f"💵 Галактика продана за {refund:,} 🪙!", show_alert=True)
        await galaxy_menu(call)
