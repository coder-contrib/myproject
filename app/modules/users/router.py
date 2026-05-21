from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import get_current_user, get_current_tenant_id
from app.modules.users.schemas import UserCreate, UserUpdate, UserResponse, RoleCreate, RoleResponse
from app.modules.users.service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserResponse)
async def create_user(
    data: UserCreate,
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    return await service.create_user(tenant_id=tenant_id, **data.model_dump())


@router.get("/", response_model=list[UserResponse])
async def list_users(
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    return await service.list_users(tenant_id)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    return await service.get_user(user_id)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    return await service.update_user(user_id, **data.model_dump(exclude_unset=True))


@router.delete("/{user_id}")
async def delete_user(
    user_id: UUID,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    await service.delete_user(user_id, deleted_by=current_user.id)
    return {"detail": "User deleted"}


@router.post("/roles", response_model=RoleResponse)
async def create_role(
    data: RoleCreate,
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    return await service.create_role(tenant_id=tenant_id, **data.model_dump())


@router.get("/roles/", response_model=list[RoleResponse])
async def list_roles(
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    return await service.list_roles(tenant_id)
