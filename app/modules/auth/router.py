from uuid import UUID
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security.dependencies import get_current_user, get_current_active_user
from app.modules.auth.schemas import (
    LoginRequest, TokenResponse, RefreshRequest, RegisterRequest,
    LogoutRequest, PasswordResetRequest, PasswordResetConfirm,
    ChangePasswordRequest, SessionResponse, APIKeyCreateRequest,
    APIKeyResponse, APIKeyCreatedResponse, UserActivationRequest,
)
from app.modules.auth.service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    ip_address = request.client.host if request.client else None
    return await service.login(
        email=data.email,
        password=data.password,
        device_info=data.device_info,
        ip_address=ip_address,
    )


@router.post("/logout")
async def logout(
    data: LogoutRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = AuthService(db)
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    await service.logout(access_token=token, refresh_token=data.refresh_token)
    return {"message": "Successfully logged out"}


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    return await service.refresh(refresh_token=data.refresh_token)


@router.post("/register", response_model=TokenResponse)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    return await service.register(
        tenant_name=data.tenant_name,
        full_name=data.full_name,
        email=data.email,
        password=data.password,
    )


@router.post("/password-reset/request")
async def request_password_reset(data: PasswordResetRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    await service.request_password_reset(email=data.email)
    return {"message": "If the email exists, a reset link has been sent"}


@router.post("/password-reset/confirm")
async def confirm_password_reset(data: PasswordResetConfirm, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    await service.confirm_password_reset(token=data.token, new_password=data.new_password)
    return {"message": "Password reset successfully"}


@router.post("/change-password")
async def change_password(
    data: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    service = AuthService(db)
    await service.change_password(
        user_id=current_user.id,
        current_password=data.current_password,
        new_password=data.new_password,
    )
    return {"message": "Password changed successfully"}


@router.get("/sessions", response_model=list[SessionResponse])
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    service = AuthService(db)
    return await service.get_sessions(user_id=current_user.id)


@router.delete("/sessions/{session_id}")
async def revoke_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    service = AuthService(db)
    await service.revoke_session(user_id=current_user.id, session_id=session_id)
    return {"message": "Session revoked"}


@router.delete("/sessions")
async def revoke_all_sessions(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    service = AuthService(db)
    payload = getattr(current_user, "_token_payload", {})
    session_id = payload.get("session_id")
    current_session = UUID(session_id) if session_id else None
    count = await service.revoke_all_sessions(
        user_id=current_user.id,
        except_session_id=current_session,
    )
    return {"message": f"Revoked {count} sessions"}


@router.post("/api-keys", response_model=APIKeyCreatedResponse)
async def create_api_key(
    data: APIKeyCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    service = AuthService(db)
    api_key, raw_key = await service.create_api_key(
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        name=data.name,
        scopes=data.scopes,
        expires_in_days=data.expires_in_days,
    )
    return APIKeyCreatedResponse(
        id=api_key.id,
        name=api_key.name,
        key=raw_key,
        key_prefix=api_key.key_prefix,
        scopes=api_key.scopes,
        expires_at=api_key.expires_at,
    )


@router.get("/api-keys", response_model=list[APIKeyResponse])
async def list_api_keys(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    service = AuthService(db)
    return await service.list_api_keys(user_id=current_user.id)


@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    key_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    service = AuthService(db)
    await service.revoke_api_key(user_id=current_user.id, key_id=key_id)
    return {"message": "API key revoked"}


@router.post("/users/{user_id}/activate")
async def activate_deactivate_user(
    user_id: UUID,
    data: UserActivationRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    service = AuthService(db)
    await service.activate_user(user_id=user_id, is_active=data.is_active)
    status = "activated" if data.is_active else "deactivated"
    return {"message": f"User {status} successfully"}
