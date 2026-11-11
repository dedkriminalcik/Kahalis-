from sqlalchemy import Column, Integer, String, BigInteger, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import datetime

Base = declarative_base()
DATABASE_URL = "sqlite+aiosqlite:///./space_game.db"

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

class User(Base):
    __tablename__ = 'users'

    id = Column(BigInteger, primary_key=True)  # Telegram ID
    username = Column(String, nullable=True)
    level = Column(Integer, default=1)
    exp = Column(Integer, default=0)
    
    # Валюта
    neutrinos = Column(BigInteger, default=1500)  # Основная валюта 🪙
    quantium = Column(Integer, default=10)        # Премиум 💎

    # Корабль и щиты (защита от урона 💥)
    ship_name = Column(String, default="Разведчик МК-1")
    attack = Column(Integer, default=15)
    defense = Column(Integer, default=10)
    health = Column(Integer, default=100)
    max_health = Column(Integer, default=100)
    shield_type = Column(String, default="Отсутствует") # Слойка/Щит от урона
    shield_power = Column(Integer, default=0)           # Прочность щита

    # Клан и Галактика
    clan_id = Column(Integer, ForeignKey('clans.id'), nullable=True)
    own_galaxy_id = Column(Integer, ForeignKey('galaxies.id'), nullable=True)

    # Таймеры
    last_work_time = Column(DateTime, default=datetime.datetime.min)
    last_bonus_time = Column(DateTime, default=datetime.datetime.min)

class Galaxy(Base):
    __tablename__ = 'galaxies'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    galaxy_type = Column(String, default="Спиральная") # Тип галактики
    owner_id = Column(BigInteger, ForeignKey('users.id'), nullable=True)
    
    defense_level = Column(Integer, default=1)   # Щиты сектора
    economy_level = Column(Integer, default=1)   # Доход налога

class Clan(Base):
    __tablename__ = 'clans'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    leader_id = Column(BigInteger, ForeignKey('users.id'))
    rating = Column(Integer, default=0)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
