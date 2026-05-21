from uuid import UUID
from fastapi import APIRouter, Depends
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
from app.modules.users.models import User

router = APIRouter(prefix="/users", tags=["users"])


@router.get("")
async def list_users(
    pagination: PaginationParams = Depends(get_pagination),
    filters: FilterParams = Depends(get_filters),
    sorting: SortParams = Depends(get_sorting),
    search: SearchParams = Depends(get_search),
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    base = select(User).where(User.tenant_id == ctx.tenant_id, User.deleted_at == None)

    base = search.apply_to_query(base, User, searchable_fields=["full_name", "email"])
    base = filters.apply_to_query(base, User)
    base = sorting.apply_to_query(base, User)

    count_stmt = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = base.offset(pagination.skip).limit(pagination.limit)
    result = await db.execute(stmt)
    users = result.scalars().all()

    data = [
        {
            "id": str(u.id),
            "full_name": u.full_name,
            "email": u.email,
            "is_active": u.is_active,
            "role_id": str(u.role_id) if u.role_id else None,
            "branch_id": str(u.branch_id) if u.branch_id else None,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }
        for u in users
    ]

    return paginated_response(data=data, total=total, page=pagination.page, per_page=pagination.per_page)


@router.get("/{user_id}")
async def get_user(
    user_id: UUID,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User).where(User.id == user_id, User.tenant_id == ctx.tenant_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="User not found")

    return success_response(data={
        "id": str(user.id),
        "full_name": user.full_name,
        "email": user.email,
        "is_active": user.is_active,
        "role_id": str(user.role_id) if user.role_id else None,
        "branch_id": str(user.branch_id) if user.branch_id else None,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None,
    })
