from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text
from .models import Base, User, UserRole
from passlib.context import CryptContext
from data.fixtures import USERS
import uuid
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./aura_wealth.db")

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await seed_users()


async def seed_users():
    async with AsyncSessionLocal() as session:
        for u in USERS:
            existing = await session.get(User, u["id"])
            if not existing:
                user = User(
                    id=u["id"],
                    email=u["email"],
                    hashed_password=pwd_context.hash(u["password"]),
                    name=u["name"],
                    role=UserRole(u["role"]),
                )
                session.add(user)
        await session.commit()


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
