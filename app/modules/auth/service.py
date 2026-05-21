from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import verify_password, create_access_token, create_refresh_token, decode_token
from app.core.exceptions.handlers import AppException
from app.modules.users.service import UserService
from app.modules.tenants.service import TenantService


class AuthService:
    def __init__(self, db: AsyncSession):
        self.user_service = UserService(db)
        self.tenant_service = TenantService(db)
        self.db = db

    async def login(self, email: str, password: str) -> dict:
        user = await self.user_service.get_user_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise AppException("Invalid email or password", status_code=401)

        if not user.is_active:
            raise AppException("Account is disabled", status_code=403)

        access_token = create_access_token(user.id, user.tenant_id)
        refresh_token = create_refresh_token(user.id)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    async def refresh(self, refresh_token: str) -> dict:
        try:
            payload = decode_token(refresh_token)
        except ValueError:
            raise AppException("Invalid refresh token", status_code=401)

        if payload.get("type") != "refresh":
            raise AppException("Invalid token type", status_code=401)

        from uuid import UUID
        user = await self.user_service.get_user(UUID(payload["sub"]))
        access_token = create_access_token(user.id, user.tenant_id)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    async def register(self, tenant_name: str, full_name: str, email: str, password: str) -> dict:
        tenant = await self.tenant_service.create_tenant(name=tenant_name)
        user = await self.user_service.create_user(
            tenant_id=tenant.id,
            full_name=full_name,
            email=email,
            password=password,
        )

        access_token = create_access_token(user.id, tenant.id)
        refresh_token = create_refresh_token(user.id)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }
