import asyncio
from datetime import date
from typing import AsyncGenerator
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.database import Base, get_db
from app.main import app
from app.models.enums import SexEnum
from app.models.patient import Patient

# In-memory SQLite engine for blazing-fast, isolated automated testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

TestAsyncSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


@pytest.fixture(scope="session")
def event_loop():
    """Create session-wide event loop for pytest-asyncio."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide isolated database session with freshly built schema per test function."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestAsyncSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """FastAPI async test client with database dependency override."""
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def sample_patient(db_session: AsyncSession) -> Patient:
    """Fixture providing a persisted test patient."""
    patient = Patient(
        first_name="Alice",
        last_name="Johnson",
        date_of_birth=date(1995, 8, 24),
        sex=SexEnum.FEMALE,
        phone_number="4155551234",
        address_line_1="456 Elm Street",
        city="San Francisco",
        state="CA",
        zip_code="94102",
        email="alice.johnson@example.com",
    )
    db_session.add(patient)
    await db_session.commit()
    await db_session.refresh(patient)
    return patient
