import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, Body
from pydantic import BaseModel, Field

from app.core.api.response import success_response, error_response

router = APIRouter(prefix="/ai", tags=["AI"])


# --- Request Models ---

class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=1000)
    context: Optional[dict] = None


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=500)
    entity_types: Optional[list[str]] = None
    limit: int = Field(default=10, ge=1, le=50)
    threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    include_summary: bool = False


class FeedbackRequest(BaseModel):
    interaction_id: str
    feature: str = Field(..., min_length=1, max_length=50)
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(default=None, max_length=2000)
    tags: Optional[list[str]] = None
    query: Optional[str] = None
    response_summary: Optional[str] = None


class ReportRequest(BaseModel):
    report_type: str = Field(..., pattern="^(executive|sales|inventory|financial|custom)$")
    period_days: int = Field(default=30, ge=1, le=365)
    branch_id: Optional[str] = None
    description: Optional[str] = None
    data_queries: Optional[list[str]] = None


class AnalyticsRequest(BaseModel):
    analysis_type: str = Field(..., pattern="^(trends|anomalies|forecast|recommendations)$")
    metric: str = Field(default="revenue")
    period_days: int = Field(default=30, ge=1, le=365)
    entity_type: Optional[str] = None
    customer_id: Optional[str] = None
    forecast_days: int = Field(default=7, ge=1, le=90)


class IndexRequest(BaseModel):
    entity_type: str = Field(..., pattern="^(product|customer|invoice)$")
    entity_id: str
    content: dict


class TemplateUpdateRequest(BaseModel):
    system_template: Optional[str] = None
    user_template: Optional[str] = None


# --- Endpoints ---

@router.post("/query")
async def ai_query(
    request: QueryRequest,
    tenant_id: str = Query(...),
    user_id: str = Query(...),
):
    from app.ai.query_assistant import QueryAssistant

    assistant = QueryAssistant()
    # In production, db session would come from dependency injection
    # For now, this demonstrates the API contract
    return success_response(
        data={
            "interaction_id": str(uuid.uuid4()),
            "status": "processed",
            "question": request.question,
            "note": "Requires database session dependency for execution",
        },
        message="Query received",
    )


@router.post("/query/suggestions")
async def ai_query_suggestions(
    tenant_id: str = Query(...),
    context: Optional[str] = Query(default=None),
):
    from app.ai.query_assistant import QueryAssistant

    assistant = QueryAssistant()
    suggestions = await assistant.suggest_questions(tenant_id, context)
    return success_response(data={"suggestions": suggestions})


@router.post("/search")
async def ai_search(
    request: SearchRequest,
    tenant_id: str = Query(...),
):
    from app.ai.search import SemanticSearch

    search = SemanticSearch()
    return success_response(
        data={
            "query": request.query,
            "entity_types": request.entity_types,
            "limit": request.limit,
            "threshold": request.threshold,
            "note": "Requires database session dependency for execution",
        },
        message="Search request received",
    )


@router.post("/search/index")
async def ai_index_entity(
    request: IndexRequest,
    tenant_id: str = Query(...),
):
    return success_response(
        data={
            "entity_type": request.entity_type,
            "entity_id": request.entity_id,
            "status": "queued",
        },
        message="Entity queued for indexing",
    )


@router.post("/analytics")
async def ai_analytics(
    request: AnalyticsRequest,
    tenant_id: str = Query(...),
):
    return success_response(
        data={
            "interaction_id": str(uuid.uuid4()),
            "analysis_type": request.analysis_type,
            "metric": request.metric,
            "period_days": request.period_days,
            "note": "Requires database session dependency for execution",
        },
        message="Analytics request received",
    )


@router.post("/reports/generate")
async def ai_generate_report(
    request: ReportRequest,
    tenant_id: str = Query(...),
):
    return success_response(
        data={
            "report_id": str(uuid.uuid4()),
            "report_type": request.report_type,
            "period_days": request.period_days,
            "status": "generating",
            "note": "Requires database session dependency for execution",
        },
        message="Report generation started",
    )


@router.post("/feedback")
async def ai_submit_feedback(
    request: FeedbackRequest,
    tenant_id: str = Query(...),
    user_id: str = Query(...),
):
    from app.ai.feedback import FeedbackEntry, feedback_collector

    entry = FeedbackEntry(
        tenant_id=tenant_id,
        user_id=user_id,
        interaction_id=request.interaction_id,
        feature=request.feature,
        rating=request.rating,
        comment=request.comment or "",
        tags=request.tags or [],
        query=request.query or "",
        response_summary=request.response_summary or "",
    )

    return success_response(
        data={
            "interaction_id": request.interaction_id,
            "rating": request.rating,
            "status": "recorded",
            "note": "Requires database session dependency for persistence",
        },
        message="Feedback recorded",
    )


@router.get("/feedback/stats")
async def ai_feedback_stats(
    tenant_id: str = Query(...),
    feature: Optional[str] = Query(default=None),
    days: int = Query(default=30, ge=1, le=365),
):
    return success_response(
        data={
            "tenant_id": tenant_id,
            "feature": feature,
            "period_days": days,
            "note": "Requires database session dependency for execution",
        },
        message="Stats request received",
    )


@router.get("/feedback/improvements/{feature}")
async def ai_improvement_suggestions(
    feature: str,
    tenant_id: str = Query(...),
):
    return success_response(
        data={
            "feature": feature,
            "note": "Requires database session dependency for execution",
        },
        message="Improvement analysis request received",
    )


@router.get("/templates")
async def list_prompt_templates(
    category: Optional[str] = Query(default=None),
):
    from app.ai.templates import prompt_registry

    templates = prompt_registry.list_templates(category=category)
    return success_response(data={"templates": templates})


@router.get("/templates/{name}")
async def get_prompt_template(name: str):
    from app.ai.templates import prompt_registry

    try:
        template = prompt_registry.get(name)
        return success_response(data={
            "name": template.name,
            "description": template.description,
            "category": template.category,
            "version": template.version,
            "variables": template.variables,
            "system_template": template.system_template,
            "user_template": template.user_template,
        })
    except KeyError:
        return error_response(message=f"Template '{name}' not found")


@router.put("/templates/{name}")
async def update_prompt_template(
    name: str,
    request: TemplateUpdateRequest,
):
    from app.ai.templates import prompt_registry

    try:
        prompt_registry.update(
            name=name,
            system_template=request.system_template,
            user_template=request.user_template,
        )
        template = prompt_registry.get(name)
        return success_response(
            data={"name": template.name, "version": template.version},
            message="Template updated",
        )
    except KeyError:
        return error_response(message=f"Template '{name}' not found")
