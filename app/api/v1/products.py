from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.tenant import TenantContext, get_tenant_context
from app.core.api import (
    PaginationParams, get_pagination,
    FilterParams, get_filters,
    SortParams, get_sorting,
    SearchParams, get_search,
)
from app.core.api.response import paginated_response, success_response
from app.modules.inventory.models import Product, Category, Warehouse

router = APIRouter(prefix="/products", tags=["products"])


class ProductCreate(BaseModel):
    name: str
    sku: str | None = None
    category_id: UUID | None = None
    sale_price: float = 0
    purchase_price: float = 0
    low_stock_threshold: int = 10

    @field_validator("sale_price", "purchase_price")
    @classmethod
    def non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Price cannot be negative")
        return v


class ProductUpdate(BaseModel):
    name: str | None = None
    sku: str | None = None
    category_id: UUID | None = None
    sale_price: float | None = None
    purchase_price: float | None = None
    low_stock_threshold: int | None = None


@router.get("")
async def list_products(
    pagination: PaginationParams = Depends(get_pagination),
    filters: FilterParams = Depends(get_filters),
    sorting: SortParams = Depends(get_sorting),
    search: SearchParams = Depends(get_search),
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    base = select(Product).where(Product.tenant_id == ctx.tenant_id, Product.deleted_at == None)

    base = search.apply_to_query(base, Product, searchable_fields=["name", "sku"])
    base = filters.apply_to_query(base, Product)
    base = sorting.apply_to_query(base, Product)

    count_stmt = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = base.offset(pagination.skip).limit(pagination.limit)
    result = await db.execute(stmt)
    products = result.scalars().all()

    data = [
        {
            "id": str(p.id),
            "name": p.name,
            "sku": p.sku,
            "category_id": str(p.category_id) if p.category_id else None,
            "sale_price": float(p.sale_price),
            "purchase_price": float(p.purchase_price),
            "average_cost": float(p.average_cost) if p.average_cost else 0,
            "low_stock_threshold": p.low_stock_threshold,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in products
    ]

    return paginated_response(data=data, total=total, page=pagination.page, per_page=pagination.per_page)


@router.post("")
async def create_product(
    data: ProductCreate,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    if data.sku:
        existing = await db.execute(
            select(Product).where(
                Product.tenant_id == ctx.tenant_id,
                Product.sku == data.sku,
                Product.deleted_at == None,
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="SKU already exists")

    product = Product(
        tenant_id=ctx.tenant_id,
        company_id=ctx.company_id,
        name=data.name,
        sku=data.sku,
        category_id=data.category_id,
        sale_price=data.sale_price,
        purchase_price=data.purchase_price,
        low_stock_threshold=data.low_stock_threshold,
        created_by=ctx.user_id,
    )
    db.add(product)
    await db.flush()
    await db.refresh(product)

    return success_response(
        data={"id": str(product.id), "name": product.name, "sku": product.sku},
        message="Product created",
    )


@router.get("/{product_id}")
async def get_product(
    product_id: UUID,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Product).where(
            Product.id == product_id,
            Product.tenant_id == ctx.tenant_id,
            Product.deleted_at == None,
        )
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return success_response(data={
        "id": str(product.id),
        "name": product.name,
        "sku": product.sku,
        "category_id": str(product.category_id) if product.category_id else None,
        "sale_price": float(product.sale_price),
        "purchase_price": float(product.purchase_price),
        "average_cost": float(product.average_cost) if product.average_cost else 0,
        "low_stock_threshold": product.low_stock_threshold,
        "version": product.version,
        "created_at": product.created_at.isoformat() if product.created_at else None,
        "updated_at": product.updated_at.isoformat() if product.updated_at else None,
    })


@router.put("/{product_id}")
async def update_product(
    product_id: UUID,
    data: ProductUpdate,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Product).where(
            Product.id == product_id,
            Product.tenant_id == ctx.tenant_id,
            Product.deleted_at == None,
        )
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(product, key, value)
    product.updated_by = ctx.user_id
    product.version += 1

    await db.flush()
    await db.refresh(product)

    return success_response(
        data={"id": str(product.id), "name": product.name, "version": product.version},
        message="Product updated",
    )


@router.delete("/{product_id}")
async def delete_product(
    product_id: UUID,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    from datetime import datetime

    result = await db.execute(
        select(Product).where(
            Product.id == product_id,
            Product.tenant_id == ctx.tenant_id,
            Product.deleted_at == None,
        )
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product.deleted_at = datetime.utcnow()
    product.deleted_by = ctx.user_id
    await db.flush()

    return success_response(message="Product deleted")
