import pytest_asyncio
from sqlalchemy import Boolean, String
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from uuid import UUID, uuid4

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(TEST_DB_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class _TestBase(DeclarativeBase):
    pass


class _TestWarehouse(_TestBase):
    __tablename__ = "warehouses"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    address: Mapped[str | None] = mapped_column(nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


@pytest_asyncio.fixture(autouse=True)
async def _create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(_TestBase.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(_TestBase.metadata.drop_all)


@pytest_asyncio.fixture
async def session():
    async with async_session() as sess:
        yield sess


@pytest_asyncio.fixture
def warehouse_repo(session: AsyncSession):
    from app.infrastructure.postgres.repos.warehouses import PostgresWarehousesRepository
    import app.infrastructure.postgres.repos.warehouses as repo_mod

    original = repo_mod.WarehouseModel
    repo_mod.WarehouseModel = _TestWarehouse
    try:
        yield PostgresWarehousesRepository(session)
    finally:
        repo_mod.WarehouseModel = original
