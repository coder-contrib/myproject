from typing import Optional

from fastapi import APIRouter, Query
from fastapi.responses import PlainTextResponse

from app.core.api.response import success_response, error_response

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])


# --- Prometheus Metrics ---

@router.get("/metrics", response_class=PlainTextResponse)
async def prometheus_metrics():
    """Prometheus-compatible metrics endpoint."""
    from app.monitoring.metrics import metrics_collector
    return PlainTextResponse(
        content=metrics_collector.expose_prometheus(),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )


@router.get("/metrics/json")
async def metrics_json():
    """All metrics in JSON format."""
    from app.monitoring.metrics import metrics_collector
    return success_response(data=metrics_collector.get_all_metrics())


# --- Performance ---

@router.get("/performance/overview")
async def performance_overview():
    """Request performance overview with percentiles."""
    from app.monitoring.performance import perf_monitor
    return success_response(data=perf_monitor.get_overview())


@router.get("/performance/endpoints")
async def performance_endpoints(
    top_n: int = Query(default=20, ge=1, le=100),
):
    """Per-endpoint performance stats."""
    from app.monitoring.performance import perf_monitor
    return success_response(data={"endpoints": perf_monitor.get_endpoint_stats(top_n)})


@router.get("/performance/slow")
async def performance_slow_requests(
    limit: int = Query(default=50, ge=1, le=200),
):
    """List slow requests above threshold."""
    from app.monitoring.performance import perf_monitor
    return success_response(data={"slow_requests": perf_monitor.get_slow_requests(limit)})


@router.get("/performance/throughput")
async def performance_throughput(
    window_minutes: int = Query(default=5, ge=1, le=60),
):
    """Request throughput (RPM) over rolling window."""
    from app.monitoring.performance import perf_monitor
    return success_response(data=perf_monitor.get_throughput(window_minutes))


# --- Error Tracking ---

@router.get("/errors")
async def list_errors(
    limit: int = Query(default=50, ge=1, le=200),
):
    """List recent tracked errors."""
    from app.monitoring.error_tracking import error_tracker
    return success_response(data={"errors": error_tracker.get_recent_errors(limit)})


@router.get("/errors/stats")
async def error_stats():
    """Error statistics and top recurring issues."""
    from app.monitoring.error_tracking import error_tracker
    return success_response(data=error_tracker.get_error_stats())


@router.get("/errors/{error_id}")
async def get_error_detail(error_id: str):
    """Get full error detail including traceback."""
    from app.monitoring.error_tracking import error_tracker
    detail = error_tracker.get_error_detail(error_id)
    if not detail:
        return error_response(message="Error not found")
    return success_response(data=detail)


# --- Audit Logs ---

@router.get("/audit")
async def query_audit_logs(
    tenant_id: str = Query(...),
    user_id: Optional[str] = Query(default=None),
    action: Optional[str] = Query(default=None),
    entity_type: Optional[str] = Query(default=None),
    entity_id: Optional[str] = Query(default=None),
    start_date: Optional[str] = Query(default=None),
    end_date: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    """Query audit logs with filters."""
    return success_response(
        data={
            "filters": {
                "tenant_id": tenant_id,
                "user_id": user_id,
                "action": action,
                "entity_type": entity_type,
            },
            "logs": [],
            "note": "Requires database session for query execution",
        },
    )


@router.get("/audit/user/{user_id}")
async def user_activity(
    user_id: str,
    tenant_id: str = Query(...),
    days: int = Query(default=30, ge=1, le=365),
):
    """Get user activity summary from audit logs."""
    return success_response(
        data={"user_id": user_id, "period_days": days, "note": "Requires database session"},
    )


@router.get("/audit/entity/{entity_type}/{entity_id}")
async def entity_history(
    entity_type: str,
    entity_id: str,
    tenant_id: str = Query(...),
    limit: int = Query(default=50, ge=1, le=200),
):
    """Get change history for a specific entity."""
    return success_response(
        data={"entity_type": entity_type, "entity_id": entity_id, "note": "Requires database session"},
    )


# --- Health & Status ---

@router.get("/health")
async def monitoring_health():
    """System health check with component status."""
    from app.monitoring.metrics import metrics_collector
    from app.monitoring.performance import perf_monitor
    from app.monitoring.error_tracking import error_tracker

    overview = perf_monitor.get_overview()
    error_stats_data = error_tracker.get_error_stats()

    return success_response(data={
        "status": "healthy",
        "components": {
            "api": {"status": "up", "requests_total": overview.get("total_requests", 0)},
            "metrics": {"status": "up", "enabled": True},
            "error_tracking": {"status": "up", "total_errors": error_stats_data.get("total_errors", 0)},
            "performance": {
                "status": "up",
                "p95_ms": overview.get("p95_ms", 0),
                "error_rate_pct": overview.get("error_rate_pct", 0),
            },
        },
    })
