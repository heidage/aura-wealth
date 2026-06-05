import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../server"))

os.environ.setdefault("JWT_SECRET", "test_secret")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from db.models import Base
from db.database import seed_users, get_db


TEST_DB_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DB_URL)
TestSession = async_sessionmaker(test_engine, expire_on_commit=False)


async def override_get_db():
    async with TestSession() as session:
        yield session


@pytest.fixture(autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    import db.database as db_module
    original_session = db_module.AsyncSessionLocal
    db_module.AsyncSessionLocal = TestSession
    await seed_users()
    db_module.AsyncSessionLocal = original_session
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def mock_orchestrator():
    with patch("api.chat.run_orchestrator", new_callable=AsyncMock) as m:
        m.return_value = "Your portfolio is well-diversified."
        yield m


@pytest.fixture
def app(mock_orchestrator):
    from main import app as fastapi_app
    fastapi_app.dependency_overrides[get_db] = override_get_db
    yield fastapi_app
    fastapi_app.dependency_overrides.clear()


@pytest.fixture
async def async_client(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
