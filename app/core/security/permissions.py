from functools import wraps
from fastapi import HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db


def require_permissions(*required: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Authentication required",
                )

            token_payload = getattr(current_user, "_token_payload", {})
            token_permissions = set(token_payload.get("permissions", []))

            if token_permissions:
                if not all(p in token_permissions for p in required):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Insufficient permissions",
                    )
            else:
                user_permissions = await _load_user_permissions(current_user, kwargs.get("db"))
                if not all(p in user_permissions for p in required):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Insufficient permissions",
                    )

            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_role(*allowed_roles: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Authentication required",
                )

            user_role = None
            if current_user.role:
                user_role = current_user.role.name

            token_payload = getattr(current_user, "_token_payload", {})
            if not user_role:
                user_role = token_payload.get("role")

            if user_role not in allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role '{user_role}' is not authorized for this action",
                )
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_scope(*required_scopes: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Authentication required",
                )

            api_key_scopes = set(getattr(current_user, "_api_key_scopes", []))
            if api_key_scopes and not all(s in api_key_scopes for s in required_scopes):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="API key lacks required scopes",
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator


async def _load_user_permissions(user, db: AsyncSession | None) -> set[str]:
    if not user.role or not user.role.permissions:
        return set()

    permissions = set()
    for rp in user.role.permissions:
        if rp.permission:
            permissions.add(rp.permission.name)
    return permissions
