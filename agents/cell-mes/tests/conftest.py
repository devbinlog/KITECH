"""Pytest configuration and fixtures for Cell-MES tests."""

import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy import event, BigInteger, Integer

from src.app.db.base import Base
from src.app.db.session import get_db
from src.app.main import app
from src.app.core.security import get_password_hash
from src.app.models import User, StdProcess, Product, Equipment


# Use SQLite for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


# Override BigInteger to Integer for SQLite (autoincrement compatibility)
@event.listens_for(Base.metadata, "before_create")
def _set_sqlite_integer(metadata, conn, **kw):
    """Convert BigInteger to Integer for SQLite to support autoincrement."""
    if conn.dialect.name == "sqlite":
        for table in metadata.tables.values():
            for column in table.columns:
                if isinstance(column.type, BigInteger):
                    column.type = Integer()


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def async_engine():
    """Create async engine for testing."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a new database session for each test."""
    async_session_maker = async_sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session_maker() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client with overridden database dependency."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        username="testuser",
        password_hash=get_password_hash("testpassword"),
        role="OPERATOR",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession) -> User:
    """Create an admin user."""
    user = User(
        username="admin",
        password_hash=get_password_hash("adminpassword"),
        role="ADMIN",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient, test_user: User) -> dict:
    """Get authentication headers for test user."""
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "testuser", "password": "testpassword"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def admin_auth_headers(client: AsyncClient, admin_user: User) -> dict:
    """Get authentication headers for admin user."""
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "admin", "password": "adminpassword"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def sample_std_process(db_session: AsyncSession) -> StdProcess:
    """Create a sample standard process."""
    process = StdProcess(
        code="STD-CUT-01",
        name="레이저 절단",
        description="레이저를 이용한 절단 공정",
    )
    db_session.add(process)
    await db_session.commit()
    await db_session.refresh(process)
    return process


@pytest_asyncio.fixture
async def sample_product(db_session: AsyncSession) -> Product:
    """Create a sample product."""
    product = Product(
        code="PROD-001",
        name="테스트 제품",
        unit="EA",
    )
    db_session.add(product)
    await db_session.commit()
    await db_session.refresh(product)
    return product


@pytest_asyncio.fixture
async def sample_equipment(db_session: AsyncSession) -> Equipment:
    """Create a sample equipment."""
    equipment = Equipment(
        eq_code="EQ-CNC-TEST-001",
        aas_id="urn:aas:cnc:test-001",
        eq_name="Test CNC",
        model_name="Test Model",
        equipment_type="CNC",
        connection_config={"ip": "192.168.1.100", "port": 502},
        spec_data={"manufacturer": "Test", "max_rpm": 20000},
        last_data={"spindle_rpm": 15000, "load_percent": 45.5},
        current_status="RUN",
    )
    db_session.add(equipment)
    await db_session.commit()
    await db_session.refresh(equipment)
    return equipment


@pytest_asyncio.fixture
async def sample_work_order(db_session: AsyncSession, sample_product: Product):
    """Create a sample work order."""
    from src.app.models.production import WorkOrder

    order = WorkOrder(
        lot_no="LOT-TEST-001",
        product_id=sample_product.id,
        target_qty=100,
        status="READY",
    )
    db_session.add(order)
    await db_session.commit()
    await db_session.refresh(order)
    return order


@pytest_asyncio.fixture
async def sample_routing(
    db_session: AsyncSession, sample_product: Product, sample_std_process: StdProcess
):
    """Create a sample process routing."""
    from src.app.models.master import ProcessRouting

    routing = ProcessRouting(
        product_id=sample_product.id,
        std_process_id=sample_std_process.id,
        sequence=10,
        remarks="Test routing",
    )
    db_session.add(routing)
    await db_session.commit()
    await db_session.refresh(routing)
    return routing


@pytest_asyncio.fixture
async def sample_scenario(db_session: AsyncSession, sample_product: Product):
    """Create a sample scenario."""
    from src.app.models.master import Scenario

    scenario = Scenario(
        code="SCN-TEST-001",
        product_id=sample_product.id,
        name="Test Scenario",
        file_path="scenarios/test.xml",
        is_active=True,
    )
    db_session.add(scenario)
    await db_session.commit()
    await db_session.refresh(scenario)
    return scenario


@pytest_asyncio.fixture
async def multiple_equipments(db_session: AsyncSession):
    """Create multiple equipments of different types."""
    equipments = []
    equipment_data = [
        ("EQ-CNC-001", "CNC-001", "CNC", "AVAILABLE"),
        ("EQ-CNC-002", "CNC-002", "CNC", "RUNNING"),
        ("EQ-ROBOT-001", "ROBOT-001", "ROBOT", "AVAILABLE"),
        ("EQ-PLC-001", "PLC-001", "PLC", "RUNNING"),
    ]

    for eq_code, name, eq_type, status in equipment_data:
        eq = Equipment(
            eq_code=eq_code,
            aas_id=f"urn:aas:{eq_type.lower()}:{name.lower()}",
            eq_name=name,
            equipment_type=eq_type,
            connection_config={"ip": "192.168.1.100"},
            current_status=status,
        )
        db_session.add(eq)
        equipments.append(eq)

    await db_session.commit()
    for eq in equipments:
        await db_session.refresh(eq)
    return equipments


@pytest.fixture(autouse=False)
def mock_middleware_http():
    """Mock httpx.AsyncClient so production endpoint middleware calls don't fail in tests."""

    class _FakeResponse:
        status_code = 201
        text = "ok"

        def json(self):
            return {}

    class _FakeAsyncClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def post(self, *args, **kwargs):
            return _FakeResponse()

        async def delete(self, *args, **kwargs):
            r = _FakeResponse()
            r.status_code = 204
            return r

    with patch("src.app.api.v1.endpoints.production.httpx.AsyncClient", return_value=_FakeAsyncClient()):
        yield
