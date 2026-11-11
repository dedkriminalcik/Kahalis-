from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.future import select
from database.models import async_session, User

router = Router()

TRANSPORTS = {
    "t1": {"name": "Пета-Байк 'Кочевник'", "price": 15000, "speed": 15},
    "t2": {"name": "Грави-Шттл 'Орион'", "price": 45000, "speed": 40},
    "t3": {"name": "Тяжелый Крейсер Транспорта", "price": 120000, "speed": 95}
}

@router.callback_query(F.data == "transport_menu")
async def transport_menu(call: CallbackQuery):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == call.from_user.id))
        user = result.scalars().first()

        text = (
            "🚀 **АНГАР КОСМИЧЕСКОГО ТРАНСПОРТА**\n\n"
            "Машины и роверы нужны для быстрого передвижения между секторами и организации рейдов на базы соперников.\n\n"
            f"Текущий транспорт: **{user.transport_name}** (Скорость/Мощность: {user.transport_speed})\n\n"
            "Выберите транспорт для покупки:"
        )

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🚀 Пета-Байк (15,000 🪙)", callback_data="buy_tr_t1")],
            [InlineKeyboardButton(text="🚀 Грави-Шттл (45,000 🪙)", callback_data="buy_tr_t2")],
            [InlineKeyboardButton(text="🚀 Тяжелый Крейсер (120,000 🪙)", callback_data="buy_tr_t3")],
            [InlineKeyboardButton(text="◀️ В меню", callback_data="back_main")]
        ])

        await call.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

@router.callback_query(F.data.startswith("buy_tr_"))
async def buy_transport_action(call: CallbackQuery):
    key = call.data.replace("buy_tr_", "")
    tr_info = TRANSPORTS.get(key)

    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == call.from_user.id))
        user = result.scalars().first()

        if user.neutrinos < tr_info["price"]:
            await call.answer("Недостаточно нейтрино (🪙) для покупки транспорта!", show_alert=True)
            return

        user.neutrinos -= tr_info["price"]
        user.transport_name = tr_info["name"]
        user.transport_speed = tr_info["speed"]
        await session.commit()

        await call.answer(f"✅ Успешно приобретен транспорт: {tr_info['name']}!", show_alert=True)
        await transport_menu(call)
