from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    role_id: UUID | None = None
    branch_id: UUID | None = None


class UserUpdate(BaseModel):
    full_name: str | None = None
    email: EmailStr | None = None
    role_id: UUID | None = None
    branch_id: UUID | None = None
    is_active: bool | None = None


class UserResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    full_name: str
    email: str
    role_id: UUID | None
    branch_id: UUID | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class RoleCreate(BaseModel):
    name: str
    description: str | None = None


class RoleResponse(BaseModel):
    id: UUID
    tenant_id: UUID | None
    name: str
    description: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
