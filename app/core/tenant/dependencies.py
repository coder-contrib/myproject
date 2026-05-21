from uuid import UUID
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.security.jwt import decode_token
from app.core.security.dependencies import security_scheme, is_token_blacklisted
from app.core.tenant.context import TenantContext


async def get_tenant_context(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
) -> TenantContext:
    try:
        payload = decode_token(credentials.credentials)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    jti = payload.get("jti")
    if jti and await is_token_blacklisted(jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
        )

    tenant_id = UUID(payload["tenant_id"])
    user_id = UUID(payload["sub"])
    role = payload.get("role")

    company_id = None
    branch_id = None

    header_company = request.headers.get("X-Company-ID")
    header_branch = request.headers.get("X-Branch-ID")

    if payload.get("company_id"):
        company_id = UUID(payload["company_id"])
    elif header_company:
        company_id = UUID(header_company)

    if payload.get("branch_id"):
        branch_id = UUID(payload["branch_id"])
    elif header_branch:
        branch_id = UUID(header_branch)

    ctx = TenantContext(
        tenant_id=tenant_id,
        company_id=company_id,
        branch_id=branch_id,
        user_id=user_id,
        role=role,
    )

    request.state.tenant_context = ctx
    return ctx


async def get_tenant_id(ctx: TenantContext = Depends(get_tenant_context)) -> UUID:
    return ctx.tenant_id


async def get_company_id(ctx: TenantContext = Depends(get_tenant_context)) -> UUID:
    if not ctx.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Company context required. Set X-Company-ID header or include company_id in token.",
        )
    return ctx.company_id


async def get_branch_id(ctx: TenantContext = Depends(get_tenant_context)) -> UUID:
    if not ctx.branch_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Branch context required. Set X-Branch-ID header or include branch_id in token.",
        )
    return ctx.branch_id


def require_tenant(func):
    """Decorator ensuring tenant context is present."""
    from functools import wraps

    @wraps(func)
    async def wrapper(*args, **kwargs):
        ctx = kwargs.get("ctx") or kwargs.get("tenant_context")
        if not ctx or not ctx.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tenant context required",
            )
        return await func(*args, **kwargs)
    return wrapper


def require_company(func):
    """Decorator ensuring company context is present."""
    from functools import wraps

    @wraps(func)
    async def wrapper(*args, **kwargs):
        ctx = kwargs.get("ctx") or kwargs.get("tenant_context")
        if not ctx or not ctx.company_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Company context required",
            )
        return await func(*args, **kwargs)
    return wrapper


def require_branch(func):
    """Decorator ensuring branch context is present."""
    from functools import wraps

    @wraps(func)
    async def wrapper(*args, **kwargs):
        ctx = kwargs.get("ctx") or kwargs.get("tenant_context")
        if not ctx or not ctx.branch_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Branch context required",
            )
        return await func(*args, **kwargs)
    return wrapper
