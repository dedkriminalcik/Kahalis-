from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.future import select
from database.models import async_session, User

router = Router()

SHIELDS = {
    "s1": {"name": "Энергетический купол", "price": 10000, "power": 100},
    "s2": {"name": "Квантовая слоика", "price": 35000, "power": 350},
    "s3": {"name": "Сверхъядерная матрица", "price": 90000, "power": 1000}
}

@router.callback_query(F.data == "shields_menu")
async def shields_menu(call: CallbackQuery):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == call.from_user.id))
        user = result.scalars().first()

        text = (
            "🛡 **ИНЖЕНЕРНЫЙ КОМПЛЕКС ЩИТОВ (СЛОЙКИ)**\n\n"
            "Установите защитное поле, через которое **не будет проходить урон от соперников 💥** во время нападений.\n\n"
            f"Текущая защита: **{user.shield_type}** (Прочность: {user.shield_power})\n\n"
            "Выберите защитный модуль для установки:"
        )

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🛡 Энерго-купол (10,000 🪙 | 100 проч.)", callback_data="buy_shield_s1")],
            [InlineKeyboardButton(text="🛡 Квантовая слоика (35,000 🪙 | 350 проч.)", callback_data="buy_shield_s2")],
            [InlineKeyboardButton(text="🛡 Ядерная матрица (90,000 🪙 | 1000 проч.)", callback_data="buy_shield_s3")],
            [InlineKeyboardButton(text="◀️ В меню", callback_data="back_main")]
        ])

        await call.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

@router.callback_query(F.data.startswith("buy_shield_"))
async def buy_shield_action(call: CallbackQuery):
    key = call.data.replace("buy_shield_", "")
    shield_info = SHIELDS.get(key)

    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == call.from_user.id))
        user = result.scalars().first()

        if user.neutrinos < shield_info["price"]:
            await call.answer("Недостаточно нейтрино (🪙) для покупки щита!", show_alert=True)
            return

        user.neutrinos -= shield_info["price"]
        user.shield_type = shield_info["name"]
        user.shield_power = shield_info["power"]
        await session.commit()

        await call.answer(f"✅ Успешно! Установлен щит: {shield_info['name']}", show_alert=True)
        await shields_menu(call)
