import datetime
import random
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.future import select
from database.models import async_session, User

router = Router()

@router.callback_query(F.data == "work_menu")
async def work_menu(call: CallbackQuery):
    text = (
        "⛏ **ЦЕНТР ЗАНЯТОСТИ КОСМОСА**\n\n"
        "Выбирай вакансию для заработка нейтрино (🪙) и повышения уровня (📈):"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🧹 Уборщик астероидов (Новичок)", callback_data="work_1")],
        [InlineKeyboardButton(text="⚙️ Инженер варп-ядер (Опытный)", callback_data="work_2")],
        [InlineKeyboardButton(text="🚀 Капитан торгового флота (Профи)", callback_data="work_3")],
        [InlineKeyboardButton(text="◀️ В меню", callback_data="back_main")]
    ])
    await call.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

@router.callback_query(F.data.in_(["work_1", "work_2", "work_3"]))
async def do_work(call: CallbackQuery):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == call.from_user.id))
        user = result.scalars().first()

        now = datetime.datetime.utcnow()
        cooldown = datetime.timedelta(seconds=45)

        if now - user.last_work_time < cooldown:
            sec = int((cooldown - (now - user.last_work_time)).total_seconds())
            await call.answer(f"⏳ Системы корабля перезаряжаются! Подождите {sec} сек.", show_alert=True)
            return

        # Награды в зависимости от выбранной работы
        w_type = call.data
        if w_type == "work_1":
            earned = random.randint(100, 250) * user.level
            exp_gain = random.randint(15, 30)
            job_name = "Уборщик астероидов"
        elif w_type == "work_2":
            earned = random.randint(300, 600) * user.level
            exp_gain = random.randint(35, 60)
            job_name = "Инженер варп-ядер"
        else:
            earned = random.randint(800, 1500) * user.level
            exp_gain = random.randint(70, 120)
            job_name = "Капитан торгового флота"

        user.neutrinos += earned
        user.exp += exp_gain
        user.last_work_time = now

        # Проверка повышения уровня
        lvl_up_msg = ""
        if user.exp >= user.level * 100:
            user.level += 1
            user.attack += 7
            user.defense += 5
            lvl_up_msg = f"\n\n🎉 **ПОВЫШЕНИЕ УРОВНЯ!** Вы достигли **{user.level} уровня**!"

        await session.commit()

        text = (
            f"🛠 **Смена завершена успешно!**\n"
            f"💼 Профессия: {job_name}\n\n"
            f"🪙 Заработано нейтрино: **+{earned:,}**\n"
            f"📈 Получено опыта: **+{exp_gain}**"
            f"{lvl_up_msg}"
        )

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⛏ Работать еще раз", callback_data=w_type)],
            [InlineKeyboardButton(text="◀️ К выбору работ", callback_data="work_menu")]
        ])

        await call.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
