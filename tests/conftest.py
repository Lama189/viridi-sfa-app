import pytest_asyncio
from decimal import Decimal
from sqlalchemy import Boolean, ForeignKey, Numeric, String
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


class _TestCategory(_TestBase):
    __tablename__ = "categories"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class _TestProduct(_TestBase):
    __tablename__ = "products"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    category_id: Mapped[UUID] = mapped_column(
        ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False,
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    volume: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False, default=Decimal("0.000"))
    weight: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False, default=Decimal("0.000"))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


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


@pytest_asyncio.fixture
def category_repo(session: AsyncSession):
    from app.infrastructure.postgres.repos.categories import PostgresCategoriesRepository
    import app.infrastructure.postgres.repos.categories as repo_mod

    original = repo_mod.CategoryModel
    repo_mod.CategoryModel = _TestCategory
    try:
        yield PostgresCategoriesRepository(session)
    finally:
        repo_mod.CategoryModel = original


@pytest_asyncio.fixture
def product_repo(session: AsyncSession):
    from app.infrastructure.postgres.repos.products import PostgresProductsRepository
    import app.infrastructure.postgres.repos.products as repo_mod

    original = repo_mod.ProductModel
    repo_mod.ProductModel = _TestProduct
    try:
        yield PostgresProductsRepository(session)
    finally:
        repo_mod.ProductModel = original
