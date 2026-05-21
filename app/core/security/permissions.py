from uuid import UUID
from functools import wraps
from fastapi import HTTPException, status


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
            user_permissions = set(getattr(current_user, "_permissions", []))
            if not all(p in user_permissions for p in required):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions",
                )
            return await func(*args, **kwargs)
        return wrapper
    return decorator
