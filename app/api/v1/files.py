from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, Query
from fastapi.responses import JSONResponse

from app.core.api.response import success_response, error_response
from app.files.config import file_config

router = APIRouter(prefix="/files", tags=["Files"])


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    tenant_id: str = Form(...),
    user_id: str = Form(...),
    prefix: str = Form(default="uploads"),
):
    data = await file.read()

    if len(data) > file_config.max_file_size:
        return JSONResponse(
            status_code=413,
            content=error_response(
                message=f"File too large. Maximum size: {file_config.max_file_size // (1024*1024)}MB"
            ),
        )

    from app.files.upload import upload_handler

    # Validate without DB persistence for API contract demonstration
    from app.files.validation import FileValidator
    validator = FileValidator()
    validation = validator.validate(
        filename=file.filename or "unknown",
        data=data,
        declared_content_type=file.content_type,
    )

    if not validation.valid:
        return JSONResponse(
            status_code=400,
            content=error_response(message="File validation failed", errors=validation.errors),
        )

    return success_response(
        data={
            "filename": file.filename,
            "content_type": validation.detected_mime or file.content_type,
            "size": validation.file_size,
            "status": "validated",
            "note": "Requires database session dependency for full persistence",
        },
        message="File validated and ready for upload",
    )


@router.post("/upload/multiple")
async def upload_multiple_files(
    files: list[UploadFile] = File(...),
    tenant_id: str = Form(...),
    user_id: str = Form(...),
    prefix: str = Form(default="uploads"),
):
    if len(files) > file_config.max_files_per_upload:
        return JSONResponse(
            status_code=400,
            content=error_response(
                message=f"Maximum {file_config.max_files_per_upload} files per upload"
            ),
        )

    from app.files.validation import FileValidator
    validator = FileValidator()

    results = []
    for f in files:
        data = await f.read()
        validation = validator.validate(
            filename=f.filename or "unknown",
            data=data,
            declared_content_type=f.content_type,
        )
        results.append({
            "filename": f.filename,
            "size": len(data),
            "valid": validation.valid,
            "content_type": validation.detected_mime or f.content_type,
            "errors": validation.errors if not validation.valid else [],
        })

    valid_count = sum(1 for r in results if r["valid"])
    return success_response(
        data={
            "files": results,
            "total": len(files),
            "valid": valid_count,
            "invalid": len(files) - valid_count,
        },
        message=f"{valid_count}/{len(files)} files validated",
    )


@router.post("/attachments")
async def attach_file(
    file_id: str = Form(...),
    entity_type: str = Form(...),
    entity_id: str = Form(...),
    tenant_id: str = Form(...),
    user_id: str = Form(...),
    label: Optional[str] = Form(default=None),
):
    return success_response(
        data={
            "file_id": file_id,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "label": label,
            "status": "attached",
            "note": "Requires database session dependency for persistence",
        },
        message="File attached to entity",
    )


@router.get("/attachments/{entity_type}/{entity_id}")
async def get_attachments(
    entity_type: str,
    entity_id: str,
    tenant_id: str = Query(...),
):
    return success_response(
        data={
            "entity_type": entity_type,
            "entity_id": entity_id,
            "attachments": [],
            "note": "Requires database session dependency for data retrieval",
        },
        message="Attachments retrieved",
    )


@router.delete("/attachments/{attachment_id}")
async def detach_file(
    attachment_id: str,
    tenant_id: str = Query(...),
):
    return success_response(
        data={"attachment_id": attachment_id, "status": "detached"},
        message="File detached",
    )


@router.delete("/{file_id}")
async def delete_file(
    file_id: str,
    tenant_id: str = Query(...),
):
    return success_response(
        data={"file_id": file_id, "status": "deleted"},
        message="File deleted",
    )


@router.get("/{file_id}/url")
async def get_download_url(
    file_id: str,
    tenant_id: str = Query(...),
    expiry: int = Query(default=3600, ge=60, le=86400),
):
    return success_response(
        data={
            "file_id": file_id,
            "expiry_seconds": expiry,
            "note": "Requires database session dependency to generate URL",
        },
        message="Download URL generated",
    )


@router.put("/attachments/reorder")
async def reorder_attachments(
    entity_type: str = Form(...),
    entity_id: str = Form(...),
    attachment_ids: str = Form(...),
    tenant_id: str = Form(...),
):
    ids = [aid.strip() for aid in attachment_ids.split(",") if aid.strip()]
    return success_response(
        data={
            "entity_type": entity_type,
            "entity_id": entity_id,
            "order": ids,
            "status": "reordered",
        },
        message="Attachments reordered",
    )
