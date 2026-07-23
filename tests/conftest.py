import pytest_asyncio
from decimal import Decimal
from sqlalchemy import BigInteger, Boolean, ForeignKey, Numeric, String
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


class _TestUser(_TestBase):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    phone: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="client")
    telegram_chat_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class _TestClient(_TestBase):
    __tablename__ = "clients"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    phone: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    telegram_chat_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class _TestEmployee(_TestBase):
    __tablename__ = "employees"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    phone: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="agent")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class _TestRetailPoint(_TestBase):
    __tablename__ = "retail_points"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    address: Mapped[str] = mapped_column(nullable=False)
    legal_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    client_type: Mapped[str] = mapped_column(String(1), nullable=False, default="C")
    landmark: Mapped[str | None] = mapped_column(nullable=True)
    contact_person: Mapped[str | None] = mapped_column(String(100), nullable=True)
    phone_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    inn: Mapped[str | None] = mapped_column(String(9), nullable=True)
    checking_account: Mapped[str | None] = mapped_column(String(20), nullable=True)
    bank_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    mfo: Mapped[str | None] = mapped_column(String(5), nullable=True)
    oked: Mapped[str | None] = mapped_column(String(5), nullable=True)
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6), nullable=True)
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6), nullable=True)
    photo_id: Mapped[UUID | None] = mapped_column(nullable=True)
    visit_mon: Mapped[bool] = mapped_column(Boolean, default=False)
    visit_tue: Mapped[bool] = mapped_column(Boolean, default=False)
    visit_wed: Mapped[bool] = mapped_column(Boolean, default=False)
    visit_thu: Mapped[bool] = mapped_column(Boolean, default=False)
    visit_fri: Mapped[bool] = mapped_column(Boolean, default=False)
    visit_sat: Mapped[bool] = mapped_column(Boolean, default=False)
    visit_sun: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by_employee_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("employees.id", ondelete="SET NULL"), nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


@pytest_asyncio.fixture
def user_repo(session: AsyncSession):
    from app.infrastructure.postgres.repos.users import PostgresUserRepository
    import app.infrastructure.postgres.repos.users as repo_mod

    original = repo_mod.UserModel
    repo_mod.UserModel = _TestUser
    try:
        yield PostgresUserRepository(session)
    finally:
        repo_mod.UserModel = original


@pytest_asyncio.fixture
def client_repo(session: AsyncSession):
    from app.infrastructure.postgres.repos.clients import PostgresClientRepository
    import app.infrastructure.postgres.repos.clients as repo_mod

    original = repo_mod.ClientModel
    repo_mod.ClientModel = _TestClient
    try:
        yield PostgresClientRepository(session)
    finally:
        repo_mod.ClientModel = original


@pytest_asyncio.fixture
def employee_repo(session: AsyncSession):
    from app.infrastructure.postgres.repos.employees import PostgresEmployeeRepository
    import app.infrastructure.postgres.repos.employees as repo_mod

    original = repo_mod.EmployeeModel
    repo_mod.EmployeeModel = _TestEmployee
    try:
        yield PostgresEmployeeRepository(session)
    finally:
        repo_mod.EmployeeModel = original


@pytest_asyncio.fixture
def retail_point_repo(session: AsyncSession):
    from app.infrastructure.postgres.repos.retail_points import PostgresRetailPointRepository
    import app.infrastructure.postgres.repos.retail_points as repo_mod

    original = repo_mod.RetailPointModel
    repo_mod.RetailPointModel = _TestRetailPoint
    try:
        yield PostgresRetailPointRepository(session)
    finally:
        repo_mod.RetailPointModel = original
