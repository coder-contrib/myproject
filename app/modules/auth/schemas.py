from pydantic import BaseModel, EmailStr, field_validator
from uuid import UUID
from datetime import datetime
import re


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    device_info: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int | None = None


class RefreshRequest(BaseModel):
    refresh_token: str


class RegisterRequest(BaseModel):
    tenant_name: str
    full_name: str
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one digit")
        return v


class LogoutRequest(BaseModel):
    refresh_token: str | None = None


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one digit")
        return v


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class SessionResponse(BaseModel):
    id: UUID
    device_info: str | None
    ip_address: str | None
    is_active: bool
    created_at: datetime
    last_activity_at: datetime | None
    expires_at: datetime

    model_config = {"from_attributes": True}


class APIKeyCreateRequest(BaseModel):
    name: str
    scopes: list[str] | None = None
    expires_in_days: int | None = None


class APIKeyResponse(BaseModel):
    id: UUID
    name: str
    key_prefix: str
    scopes: str | None
    is_active: bool
    created_at: datetime
    expires_at: datetime | None
    last_used_at: datetime | None

    model_config = {"from_attributes": True}


class APIKeyCreatedResponse(BaseModel):
    id: UUID
    name: str
    key: str
    key_prefix: str
    scopes: str | None
    expires_at: datetime | None


class UserActivationRequest(BaseModel):
    is_active: bool
    reason: str | None = None
