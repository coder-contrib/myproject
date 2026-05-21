from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.api.response import success_response, error_response

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    tenant_id: UUID


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


@router.post("/login")
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    from app.modules.users.models import User
    from app.core.security import verify_password, create_access_token, create_refresh_token

    result = await db.execute(select(User).where(User.email == data.email, User.is_active == True))
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token = create_access_token(user_id=str(user.id), tenant_id=str(user.tenant_id))
    refresh_token = create_refresh_token(user_id=str(user.id))

    return success_response(
        data={
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": 3600,
            "user": {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "tenant_id": str(user.tenant_id),
            },
        },
        message="Login successful",
    )


@router.post("/register")
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    from app.modules.users.models import User
    from app.core.security import hash_password

    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = User(
        full_name=data.full_name,
        email=data.email,
        password_hash=hash_password(data.password),
        tenant_id=data.tenant_id,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    return success_response(
        data={"id": str(user.id), "email": user.email, "full_name": user.full_name},
        message="Registration successful",
    )


@router.post("/refresh")
async def refresh_token(data: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    from app.core.security import decode_refresh_token, create_access_token

    payload = decode_refresh_token(data.refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    access_token = create_access_token(
        user_id=payload["user_id"],
        tenant_id=payload.get("tenant_id", ""),
    )

    return success_response(
        data={"access_token": access_token, "token_type": "bearer", "expires_in": 3600},
        message="Token refreshed",
    )


@router.post("/logout")
async def logout(db: AsyncSession = Depends(get_db)):
    return success_response(message="Logged out successfully")
