from typing import Optional

from fastapi import APIRouter, Query, Body
from pydantic import BaseModel, Field

from app.core.api.response import success_response, error_response
from app.webhooks.events import WEBHOOK_EVENTS

router = APIRouter(prefix="/webhooks", tags=["Webhooks & Integrations"])


# --- Request Models ---

class WebhookCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    url: str = Field(..., min_length=10)
    events: list[str] = Field(..., min_length=1)
    headers: Optional[dict] = None


class WebhookUpdateRequest(BaseModel):
    name: Optional[str] = Field(default=None, max_length=200)
    url: Optional[str] = None
    events: Optional[list[str]] = None
    is_active: Optional[bool] = None
    headers: Optional[dict] = None


class IntegrationCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    provider: str = Field(..., pattern="^(slack|email|payment|shipping|accounting)$")
    base_url: str = Field(..., min_length=5)
    auth_type: str = Field(..., pattern="^(api_key|oauth2|basic|bearer)$")
    credentials: dict = Field(default_factory=dict)
    headers: Optional[dict] = None
    metadata: Optional[dict] = None


class WebhookTestRequest(BaseModel):
    event_type: str = Field(default="system.test")
    payload: dict = Field(default_factory=lambda: {"test": True, "message": "Test delivery"})


# --- Webhook Endpoints ---

@router.get("/events")
async def list_webhook_events():
    """List all available webhook event types."""
    return success_response(
        data={
            "events": [
                {"event": event, "description": desc}
                for event, desc in WEBHOOK_EVENTS.items()
            ],
            "total": len(WEBHOOK_EVENTS),
        },
    )


@router.post("")
async def create_webhook(
    request: WebhookCreateRequest,
    tenant_id: str = Query(...),
    user_id: str = Query(...),
):
    # Validate event types
    invalid = [e for e in request.events if e not in WEBHOOK_EVENTS and e != "*"]
    if invalid:
        return error_response(message=f"Invalid event types: {invalid}")

    from app.webhooks.signature import WebhookSignature
    secret = WebhookSignature.generate_secret()

    return success_response(
        data={
            "name": request.name,
            "url": request.url,
            "events": request.events,
            "secret": secret,
            "is_active": True,
            "note": "Requires database session for persistence",
        },
        message="Webhook created",
    )


@router.get("")
async def list_webhooks(
    tenant_id: str = Query(...),
    active_only: bool = Query(default=False),
):
    return success_response(
        data={"webhooks": [], "note": "Requires database session"},
    )


@router.get("/{webhook_id}")
async def get_webhook(
    webhook_id: str,
    tenant_id: str = Query(...),
):
    return success_response(
        data={"webhook_id": webhook_id, "note": "Requires database session"},
    )


@router.put("/{webhook_id}")
async def update_webhook(
    webhook_id: str,
    request: WebhookUpdateRequest,
    tenant_id: str = Query(...),
):
    if request.events:
        invalid = [e for e in request.events if e not in WEBHOOK_EVENTS and e != "*"]
        if invalid:
            return error_response(message=f"Invalid event types: {invalid}")

    return success_response(
        data={"webhook_id": webhook_id, "status": "updated"},
        message="Webhook updated",
    )


@router.delete("/{webhook_id}")
async def delete_webhook(
    webhook_id: str,
    tenant_id: str = Query(...),
):
    return success_response(
        data={"webhook_id": webhook_id, "status": "deleted"},
        message="Webhook deleted",
    )


@router.post("/{webhook_id}/test")
async def test_webhook(
    webhook_id: str,
    request: WebhookTestRequest,
    tenant_id: str = Query(...),
):
    return success_response(
        data={
            "webhook_id": webhook_id,
            "event_type": request.event_type,
            "status": "test_delivery_queued",
        },
        message="Test delivery queued",
    )


@router.post("/{webhook_id}/rotate-secret")
async def rotate_webhook_secret(
    webhook_id: str,
    tenant_id: str = Query(...),
):
    from app.webhooks.signature import WebhookSignature
    new_secret = WebhookSignature.generate_secret()

    return success_response(
        data={
            "webhook_id": webhook_id,
            "new_secret": new_secret,
            "note": "Requires database session for persistence",
        },
        message="Secret rotated",
    )


@router.get("/{webhook_id}/deliveries")
async def get_delivery_log(
    webhook_id: str,
    tenant_id: str = Query(...),
    status: Optional[str] = Query(default=None, pattern="^(pending|delivered|retrying|failed)$"),
    limit: int = Query(default=50, ge=1, le=200),
):
    return success_response(
        data={"webhook_id": webhook_id, "deliveries": [], "note": "Requires database session"},
    )


@router.get("/stats/overview")
async def webhook_stats(
    tenant_id: str = Query(...),
    days: int = Query(default=7, ge=1, le=90),
):
    return success_response(
        data={"period_days": days, "stats": {}, "note": "Requires database session"},
    )


# --- Integration Endpoints ---

@router.post("/integrations")
async def create_integration(
    request: IntegrationCreateRequest,
    tenant_id: str = Query(...),
):
    from app.webhooks.integrations import integration_manager

    integration = integration_manager.register(
        name=request.name,
        provider=request.provider,
        base_url=request.base_url,
        auth_type=request.auth_type,
        credentials=request.credentials,
        headers=request.headers,
        metadata=request.metadata,
    )

    return success_response(
        data={
            "name": request.name,
            "provider": request.provider,
            "base_url": request.base_url,
            "auth_type": request.auth_type,
            "is_active": True,
        },
        message="Integration registered",
    )


@router.get("/integrations")
async def list_integrations():
    from app.webhooks.integrations import integration_manager
    return success_response(
        data={"integrations": integration_manager.list_integrations()},
    )


@router.get("/integrations/{name}/health")
async def integration_health_check(name: str):
    from app.webhooks.integrations import integration_manager

    integration = integration_manager.get(name)
    if not integration:
        return error_response(message=f"Integration '{name}' not found")

    result = await integration.health_check()
    return success_response(data={"name": name, "health": result})


@router.delete("/integrations/{name}")
async def remove_integration(name: str):
    from app.webhooks.integrations import integration_manager

    removed = integration_manager.remove(name)
    if not removed:
        return error_response(message=f"Integration '{name}' not found")

    return success_response(
        data={"name": name, "status": "removed"},
        message="Integration removed",
    )


# --- Signature Verification Endpoint ---

@router.post("/verify-signature")
async def verify_webhook_signature(
    payload: str = Body(...),
    signature: str = Query(...),
    timestamp: int = Query(...),
    secret: str = Query(...),
):
    from app.webhooks.signature import WebhookSignature

    is_valid = WebhookSignature.verify(
        payload=payload,
        secret=secret,
        signature=signature,
        timestamp=timestamp,
    )

    return success_response(
        data={"valid": is_valid},
        message="Signature valid" if is_valid else "Signature invalid",
    )
