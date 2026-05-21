from uuid import UUID
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security.jwt import (
    verify_password, hash_password, create_access_token, create_refresh_token,
    decode_token, hash_token, generate_password_reset_token, generate_api_key,
    MAX_LOGIN_ATTEMPTS, LOCKOUT_MINUTES,
)
from app.core.security.dependencies import blacklist_token
from app.core.config import get_settings
from app.core.exceptions.handlers import AppException
from app.modules.users.models import User, UserSession, APIKey, PasswordResetToken, RolePermission
from app.modules.users.service import UserService
from app.modules.tenants.service import TenantService

settings = get_settings()


class AuthService:
    def __init__(self, db: AsyncSession):
        self.user_service = UserService(db)
        self.tenant_service = TenantService(db)
        self.db = db

    async def login(self, email: str, password: str, device_info: str | None = None, ip_address: str | None = None) -> dict:
        user = await self.user_service.get_user_by_email(email)
        if not user:
            raise AppException("Invalid email or password", status_code=401)

        if user.locked_until and user.locked_until > datetime.now(timezone.utc):
            remaining = int((user.locked_until - datetime.now(timezone.utc)).total_seconds() / 60)
            raise AppException(f"Account locked. Try again in {remaining} minutes", status_code=423)

        if not verify_password(password, user.password_hash):
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= MAX_LOGIN_ATTEMPTS:
                user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=LOCKOUT_MINUTES)
            await self.db.commit()
            raise AppException("Invalid email or password", status_code=401)

        if not user.is_active:
            raise AppException("Account is disabled", status_code=403)

        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login_at = datetime.now(timezone.utc)
        await self.db.commit()

        permissions = await self._get_user_permissions(user)
        role_name = user.role.name if user.role else None

        session = await self._create_session(user, device_info, ip_address)

        access_token = create_access_token(
            user.id, user.tenant_id,
            role=role_name,
            permissions=permissions,
            session_id=session.id,
        )
        refresh_token = create_refresh_token(user.id, user.tenant_id)

        session.refresh_token_hash = hash_token(refresh_token)
        await self.db.commit()

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    async def logout(self, access_token: str, refresh_token: str | None = None) -> None:
        try:
            payload = decode_token(access_token)
            jti = payload.get("jti")
            exp = payload.get("exp")
            if jti and exp:
                ttl = int(exp - datetime.now(timezone.utc).timestamp())
                if ttl > 0:
                    await blacklist_token(jti, ttl)

            session_id = payload.get("session_id")
            if session_id:
                await self.db.execute(
                    update(UserSession)
                    .where(UserSession.id == UUID(session_id))
                    .values(is_active=False)
                )
        except ValueError:
            pass

        if refresh_token:
            token_hash = hash_token(refresh_token)
            await self.db.execute(
                update(UserSession)
                .where(UserSession.refresh_token_hash == token_hash)
                .values(is_active=False)
            )

        await self.db.commit()

    async def refresh(self, refresh_token: str) -> dict:
        try:
            payload = decode_token(refresh_token)
        except ValueError:
            raise AppException("Invalid refresh token", status_code=401)

        if payload.get("type") != "refresh":
            raise AppException("Invalid token type", status_code=401)

        token_hash = hash_token(refresh_token)
        result = await self.db.execute(
            select(UserSession).where(
                UserSession.refresh_token_hash == token_hash,
                UserSession.is_active == True,
            )
        )
        session = result.scalar_one_or_none()
        if not session:
            raise AppException("Session expired or revoked", status_code=401)

        if session.expires_at < datetime.now(timezone.utc):
            session.is_active = False
            await self.db.commit()
            raise AppException("Session expired", status_code=401)

        user = await self.user_service.get_user(UUID(payload["sub"]))
        if not user.is_active:
            raise AppException("Account is disabled", status_code=403)

        permissions = await self._get_user_permissions(user)
        role_name = user.role.name if user.role else None

        new_access_token = create_access_token(
            user.id, user.tenant_id,
            role=role_name,
            permissions=permissions,
            session_id=session.id,
        )
        new_refresh_token = create_refresh_token(user.id, user.tenant_id)

        session.refresh_token_hash = hash_token(new_refresh_token)
        session.last_activity_at = datetime.now(timezone.utc)
        await self.db.commit()

        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    async def register(self, tenant_name: str, full_name: str, email: str, password: str) -> dict:
        tenant = await self.tenant_service.create_tenant(name=tenant_name)
        user = await self.user_service.create_user(
            tenant_id=tenant.id,
            full_name=full_name,
            email=email,
            password=password,
        )

        permissions = await self._get_user_permissions(user)
        role_name = user.role.name if user.role else None

        session = await self._create_session(user, None, None)

        access_token = create_access_token(
            user.id, tenant.id,
            role=role_name,
            permissions=permissions,
            session_id=session.id,
        )
        refresh_token = create_refresh_token(user.id, tenant.id)

        session.refresh_token_hash = hash_token(refresh_token)
        await self.db.commit()

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    async def request_password_reset(self, email: str) -> str | None:
        user = await self.user_service.get_user_by_email(email)
        if not user:
            return None

        token = generate_password_reset_token()
        reset = PasswordResetToken(
            user_id=user.id,
            token_hash=hash_token(token),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        self.db.add(reset)
        await self.db.commit()
        return token

    async def confirm_password_reset(self, token: str, new_password: str) -> None:
        token_hash = hash_token(token)
        result = await self.db.execute(
            select(PasswordResetToken).where(
                PasswordResetToken.token_hash == token_hash,
                PasswordResetToken.used_at == None,
            )
        )
        reset = result.scalar_one_or_none()

        if not reset:
            raise AppException("Invalid or expired reset token", status_code=400)

        if reset.expires_at < datetime.now(timezone.utc):
            raise AppException("Reset token has expired", status_code=400)

        user = await self.user_service.get_user(reset.user_id)
        user.password_hash = hash_password(new_password)
        user.password_changed_at = datetime.now(timezone.utc)
        reset.used_at = datetime.now(timezone.utc)

        await self.db.execute(
            update(UserSession)
            .where(UserSession.user_id == user.id, UserSession.is_active == True)
            .values(is_active=False)
        )

        await self.db.commit()

    async def change_password(self, user_id: UUID, current_password: str, new_password: str) -> None:
        user = await self.user_service.get_user(user_id)

        if not verify_password(current_password, user.password_hash):
            raise AppException("Current password is incorrect", status_code=400)

        user.password_hash = hash_password(new_password)
        user.password_changed_at = datetime.now(timezone.utc)
        await self.db.commit()

    async def activate_user(self, user_id: UUID, is_active: bool) -> None:
        user = await self.user_service.get_user(user_id)
        user.is_active = is_active

        if not is_active:
            await self.db.execute(
                update(UserSession)
                .where(UserSession.user_id == user.id, UserSession.is_active == True)
                .values(is_active=False)
            )

        await self.db.commit()

    async def get_sessions(self, user_id: UUID) -> list[UserSession]:
        result = await self.db.execute(
            select(UserSession).where(
                UserSession.user_id == user_id,
                UserSession.is_active == True,
            ).order_by(UserSession.created_at.desc())
        )
        return list(result.scalars().all())

    async def revoke_session(self, user_id: UUID, session_id: UUID) -> None:
        result = await self.db.execute(
            select(UserSession).where(
                UserSession.id == session_id,
                UserSession.user_id == user_id,
            )
        )
        session = result.scalar_one_or_none()
        if not session:
            raise AppException("Session not found", status_code=404)

        session.is_active = False
        await self.db.commit()

    async def revoke_all_sessions(self, user_id: UUID, except_session_id: UUID | None = None) -> int:
        stmt = (
            update(UserSession)
            .where(UserSession.user_id == user_id, UserSession.is_active == True)
            .values(is_active=False)
        )
        if except_session_id:
            stmt = stmt.where(UserSession.id != except_session_id)

        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount

    async def create_api_key(
        self, user_id: UUID, tenant_id: UUID, name: str,
        scopes: list[str] | None = None, expires_in_days: int | None = None,
    ) -> tuple[APIKey, str]:
        raw_key = generate_api_key()
        key_prefix = raw_key[:8]
        key_hash = hash_token(raw_key)

        expires_at = None
        if expires_in_days:
            expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)

        api_key = APIKey(
            user_id=user_id,
            tenant_id=tenant_id,
            name=name,
            key_prefix=key_prefix,
            key_hash=key_hash,
            scopes=",".join(scopes) if scopes else None,
            expires_at=expires_at,
        )
        self.db.add(api_key)
        await self.db.commit()
        await self.db.refresh(api_key)

        return api_key, raw_key

    async def list_api_keys(self, user_id: UUID) -> list[APIKey]:
        result = await self.db.execute(
            select(APIKey).where(APIKey.user_id == user_id).order_by(APIKey.created_at.desc())
        )
        return list(result.scalars().all())

    async def revoke_api_key(self, user_id: UUID, key_id: UUID) -> None:
        result = await self.db.execute(
            select(APIKey).where(APIKey.id == key_id, APIKey.user_id == user_id)
        )
        api_key = result.scalar_one_or_none()
        if not api_key:
            raise AppException("API key not found", status_code=404)

        api_key.is_active = False
        await self.db.commit()

    async def _create_session(self, user: User, device_info: str | None, ip_address: str | None) -> UserSession:
        session = UserSession(
            user_id=user.id,
            tenant_id=user.tenant_id,
            refresh_token_hash="pending",
            device_info=device_info,
            ip_address=ip_address,
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            last_activity_at=datetime.now(timezone.utc),
        )
        self.db.add(session)
        await self.db.flush()
        return session

    async def _get_user_permissions(self, user: User) -> list[str]:
        if not user.role_id:
            return []

        result = await self.db.execute(
            select(RolePermission).where(RolePermission.role_id == user.role_id)
        )
        role_permissions = result.scalars().all()
        permissions = []
        for rp in role_permissions:
            if rp.permission:
                permissions.append(rp.permission.name)
        return permissions
