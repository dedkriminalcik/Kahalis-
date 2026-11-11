import random
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.future import select
from database.models import async_session, User, Galaxy

router = Router()

@router.callback_query(F.data == "raids_menu")
async def raids_menu(call: CallbackQuery):
    text = (
        "💥 **ЗАКРЫТЫЙ СЕКТОР РЕЙДОВ**\n\n"
        "Используйте свой транспорт 🚀 для нападения на базы соперников.\n"
        "• Если у соперника есть **щит (слойка)** — урон поглотится.\n"
        "• Если щит пробит, вы заберете **часть ресурсов (до 30%)** 📦 прямо с его баланса!"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎯 Совершить набег на случайную базу", callback_data="execute_raid")],
        [InlineKeyboardButton(text="◀️ В меню", callback_data="back_main")]
    ])
    await call.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

@router.callback_query(F.data == "execute_raid")
async def execute_raid(call: CallbackQuery):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == call.from_user.id))
        attacker = result.scalars().first()

        # Ищем случайную чужую галактику для грабежа
        g_res = await session.execute(select(Galaxy).where(Galaxy.owner_id != attacker.id))
        target_galaxies = g_res.scalars().all()

        if not target_galaxies:
            await call.answer("В космосе пока нет чужих баз для грабежа! Попробуйте позже.", show_alert=True)
            return

        target_gal = random.choice(target_galaxies)
        
        # Находим владельца галактики
        u_res = await session.execute(select(User).where(User.id == target_gal.owner_id))
        defender = u_res.scalars().first()

        if not defender:
            await call.answer("Сектор пустует.", show_alert=True)
            return

        # Проверка защиты (слойки)
        if defender.shield_power > 0:
            defender.shield_power -= max(5, attacker.attack // 2)
            if defender.shield_power < 0:
                defender.shield_power = 0
            await session.commit()
            
            res_text = (
                f"🛡 **НАПАДЕНИЕ ОТБИТО ЩИТОМ!**\n\n"
                f"Вы атаковали сектор `{target_gal.name}`, но у противника установлена защита: **{defender.shield_type}**.\n"
                f"Щит противника поглотил весь урон 💥 (осталось прочности: {defender.shield_power}). Ресурсы не украдены."
            )
        else:
            # Успешный грабеж части ресурсов (до 30%)
            loot = int(defender.neutrinos * 0.25)
            if loot < 100:
                loot = 500 # минимальный куш
            
            if defender.neutrinos >= loot:
                defender.neutrinos -= loot
            else:
                loot = defender.neutrinos
                defender.neutrinos = 0

            attacker.neutrinos += loot
            await session.commit()

            res_text = (
                f"💥 **РЕЙД ПРОШЕЛ УСПЕШНО!**\n\n"
                f"Вы пробили оборону галактики `{target_gal.name}` пилота `{defender.username}`!\n"
                f"📦 Вы успешно вывезли часть чужих ресурсов: **+{loot:,} нейтрино (🪙)**!"
            )

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💥 Совершить еще рейд", callback_data="execute_raid")],
            [InlineKeyboardButton(text="◀️ В меню", callback_data="back_main")]
        ])

        await call.message.edit_text(res_text, reply_markup=kb, parse_mode="Markdown")
