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
    credits = Column(BigInteger, default=1000)      # Валюта
    dark_matter = Column(Integer, default=10)       # Премиум-валюта

    # Боевые характеристики корабля
    ship_name = Column(String, default="Разведчик-1")
    attack = Column(Integer, default=10)
    defense = Column(Integer, default=5)
    health = Column(Integer, default=100)
    max_health = Column(Integer, default=100)

    # Привязка к Клану и Галактике
    clan_id = Column(Integer, ForeignKey('clans.id'), nullable=True)
    own_galaxy_id = Column(Integer, ForeignKey('galaxies.id'), nullable=True)

    # Кулдаун работы (защита от спама)
    last_work_time = Column(DateTime, default=datetime.datetime.min)

class Galaxy(Base):
    __tablename__ = 'galaxies'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    owner_id = Column(BigInteger, ForeignKey('users.id'), nullable=True)
    clan_owner_id = Column(Integer, ForeignKey('clans.id'), nullable=True)

    defense_level = Column(Integer, default=1)   # Щиты и оборонительные форпосты
    economy_level = Column(Integer, default=1)   # Уровень дохода/пассивного налога
    is_clan_territory = Column(Boolean, default=False)

class Clan(Base):
    __tablename__ = 'clans'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    leader_id = Column(BigInteger, ForeignKey('users.id'))
    rating = Column(Integer, default=0)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
