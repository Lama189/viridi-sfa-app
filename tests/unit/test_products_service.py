from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.api.v1.schemas.inventory import ProductCreate, ProductUpdate
from app.application.services.products import ProductsService as ProductService
from app.domain.entities.inventory import Category, Product


@pytest.fixture
def mock_uow():
    uow = AsyncMock()
    uow.categories = AsyncMock()
    uow.products = AsyncMock()
    uow.commit = AsyncMock()
    return uow


@pytest.fixture
def service(mock_uow):
    return ProductService(mock_uow)


# --- create_product ---


@pytest.mark.asyncio
async def test_create_product_success(service, mock_uow):
    cat = Category(name="Fertilizers", id=uuid4())
    mock_uow.categories.get_by_id.return_value = cat
    mock_uow.products.exists_by.return_value = False

    dto = ProductCreate(
        name="NPK-10",
        price=Decimal("150.00"),
        category_id=cat.id,
        items_in_box=20,
    )
    result = await service.create_product(dto)

    assert result.name == "NPK-10"
    assert result.category_id == cat.id
    assert result.price == Decimal("150.00")
    assert result.items_in_box == 20
    mock_uow.products.add.assert_awaited_once()
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_product_category_not_found(service, mock_uow):
    mock_uow.categories.get_by_id.return_value = None

    dto = ProductCreate(
        name="X",
        price=Decimal("10.00"),
        category_id=uuid4(),
    )
    with pytest.raises(ValueError, match="not found"):
        await service.create_product(dto)


@pytest.mark.asyncio
async def test_create_product_category_inactive(service, mock_uow):
    cat = Category(name="Inactive", is_active=False)
    mock_uow.categories.get_by_id.return_value = cat

    dto = ProductCreate(
        name="X",
        price=Decimal("10.00"),
        category_id=cat.id,
    )
    with pytest.raises(ValueError, match="inactive"):
        await service.create_product(dto)


@pytest.mark.asyncio
async def test_create_product_duplicate_name(service, mock_uow):
    cat = Category(name="Cat")
    mock_uow.categories.get_by_id.return_value = cat
    mock_uow.products.exists_by.return_value = True

    dto = ProductCreate(
        name="Duplicate",
        price=Decimal("10.00"),
        category_id=cat.id,
    )
    with pytest.raises(ValueError, match="already exists"):
        await service.create_product(dto)

    mock_uow.products.add.assert_not_awaited()


# --- get_by_id ---


@pytest.mark.asyncio
async def test_get_by_id_found(service, mock_uow):
    uid = uuid4()
    mock_uow.products.get_by_id.return_value = Product(
        category_id=uuid4(),
        name="X",
        price=Decimal("10.00"),
        id=uid,
    )

    result = await service.get_by_id(uid)
    assert result is not None
    assert result.name == "X"


@pytest.mark.asyncio
async def test_get_by_id_not_found(service, mock_uow):
    mock_uow.products.get_by_id.return_value = None

    result = await service.get_by_id(uuid4())
    assert result is None


# --- get_all_products ---


@pytest.mark.asyncio
async def test_get_all_products(service, mock_uow):
    mock_uow.products.list_all.return_value = [
        Product(category_id=uuid4(), name="A", price=Decimal("1.00")),
        Product(category_id=uuid4(), name="B", price=Decimal("2.00")),
    ]

    result = await service.get_all_products(only_active=True)
    assert len(result) == 2
    mock_uow.products.list_all.assert_awaited_once_with(True)


# --- update_product ---


@pytest.mark.asyncio
async def test_update_product_success(service, mock_uow):
    cat = Category(name="Cat", id=uuid4())
    prod = Product(category_id=cat.id, name="Old", price=Decimal("10.00"))
    mock_uow.products.get_by_id.return_value = prod

    dto = ProductUpdate(name="New", price=Decimal("99.99"), items_in_box=10)
    result = await service.update_product(prod.id, dto)

    assert result.name == "New"
    assert result.price == Decimal("99.99")
    assert result.items_in_box == 10
    mock_uow.products.update.assert_awaited_once()
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_product_not_found(service, mock_uow):
    mock_uow.products.get_by_id.return_value = None

    dto = ProductUpdate(name="X")
    with pytest.raises(ValueError, match="not found"):
        await service.update_product(uuid4(), dto)


@pytest.mark.asyncio
async def test_update_product_change_category(service, mock_uow):
    old_cat = Category(name="Old", id=uuid4())
    new_cat = Category(name="New", id=uuid4())
    prod = Product(category_id=old_cat.id, name="P", price=Decimal("10.00"))

    mock_uow.products.get_by_id.return_value = prod
    mock_uow.categories.get_by_id.return_value = new_cat

    dto = ProductUpdate(category_id=new_cat.id)
    result = await service.update_product(prod.id, dto)

    assert result.category_id == new_cat.id
    mock_uow.categories.get_by_id.assert_awaited_once_with(new_cat.id)


@pytest.mark.asyncio
async def test_update_product_category_not_found(service, mock_uow):
    prod = Product(category_id=uuid4(), name="P", price=Decimal("10.00"))
    mock_uow.products.get_by_id.return_value = prod
    mock_uow.categories.get_by_id.return_value = None

    dto = ProductUpdate(category_id=uuid4())
    with pytest.raises(ValueError, match="not found"):
        await service.update_product(prod.id, dto)


@pytest.mark.asyncio
async def test_update_product_category_inactive(service, mock_uow):
    prod = Product(category_id=uuid4(), name="P", price=Decimal("10.00"))
    inactive_cat = Category(name="Inactive", is_active=False)
    mock_uow.products.get_by_id.return_value = prod
    mock_uow.categories.get_by_id.return_value = inactive_cat

    dto = ProductUpdate(category_id=inactive_cat.id)
    with pytest.raises(ValueError, match="inactive"):
        await service.update_product(prod.id, dto)


@pytest.mark.asyncio
async def test_update_product_is_active(service, mock_uow):
    prod = Product(
        category_id=uuid4(), name="P", price=Decimal("10.00"), is_active=True
    )
    mock_uow.products.get_by_id.return_value = prod

    dto = ProductUpdate(is_active=False)
    result = await service.update_product(prod.id, dto)

    assert result.is_active is False


# --- delete_product ---


@pytest.mark.asyncio
async def test_delete_product_success(service, mock_uow):
    prod = Product(category_id=uuid4(), name="Del", price=Decimal("10.00"))
    mock_uow.products.get_by_id.return_value = prod

    await service.delete_product(prod.id)

    mock_uow.products.delete.assert_awaited_once()
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_product_not_found(service, mock_uow):
    mock_uow.products.get_by_id.return_value = None

    with pytest.raises(ValueError, match="not found"):
        await service.delete_product(uuid4())

    mock_uow.products.delete.assert_not_awaited()
