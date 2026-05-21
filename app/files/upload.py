import uuid
import logging
from typing import Optional
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.files.storage import StorageProvider, get_storage, StoredFile
from app.files.validation import FileValidator, ValidationResult

logger = logging.getLogger("files.upload")


class FileUploadHandler:
    """Handles file upload processing: validation, storage, and record creation."""

    def __init__(self):
        self.validator = FileValidator()
        self._storage: Optional[StorageProvider] = None

    @property
    def storage(self) -> StorageProvider:
        if self._storage is None:
            self._storage = get_storage()
        return self._storage

    async def upload_file(
        self,
        db: AsyncSession,
        tenant_id: str,
        user_id: str,
        filename: str,
        data: bytes,
        content_type: Optional[str] = None,
        prefix: str = "uploads",
        metadata: Optional[dict] = None,
    ) -> dict:
        # Validate the file
        validation = self.validator.validate(
            filename=filename,
            data=data,
            declared_content_type=content_type,
        )

        if not validation.valid:
            return {
                "success": False,
                "errors": validation.errors,
            }

        # Generate storage key and upload
        key = self.storage.generate_key(tenant_id, filename, prefix)
        mime = validation.detected_mime or content_type or "application/octet-stream"

        stored = await self.storage.upload(key, data, mime)

        # Create database record
        file_id = str(uuid.uuid4())
        await db.execute(text(
            "INSERT INTO files (id, tenant_id, uploaded_by, filename, storage_key, "
            "content_type, size, etag, metadata, created_at) "
            "VALUES (:id, :tenant_id, :user_id, :filename, :key, "
            ":content_type, :size, :etag, :metadata, :now)"
        ), {
            "id": file_id,
            "tenant_id": tenant_id,
            "user_id": user_id,
            "filename": filename,
            "key": key,
            "content_type": mime,
            "size": stored.size,
            "etag": stored.etag,
            "metadata": metadata or {},
            "now": datetime.utcnow(),
        })
        await db.commit()

        logger.info("File uploaded: id=%s key=%s user=%s", file_id, key, user_id)

        return {
            "success": True,
            "file": {
                "id": file_id,
                "filename": filename,
                "content_type": mime,
                "size": stored.size,
                "storage_key": key,
            },
        }

    async def upload_multiple(
        self,
        db: AsyncSession,
        tenant_id: str,
        user_id: str,
        files: list[dict],
        prefix: str = "uploads",
    ) -> dict:
        from app.files.config import file_config

        if len(files) > file_config.max_files_per_upload:
            return {
                "success": False,
                "errors": [f"Maximum {file_config.max_files_per_upload} files per upload"],
            }

        results = []
        for file_data in files:
            result = await self.upload_file(
                db=db,
                tenant_id=tenant_id,
                user_id=user_id,
                filename=file_data["filename"],
                data=file_data["data"],
                content_type=file_data.get("content_type"),
                prefix=prefix,
            )
            results.append(result)

        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        return {
            "success": len(failed) == 0,
            "uploaded": [r["file"] for r in successful],
            "failed": [{"errors": r["errors"]} for r in failed],
            "total": len(files),
            "successful_count": len(successful),
            "failed_count": len(failed),
        }

    async def delete_file(
        self,
        db: AsyncSession,
        tenant_id: str,
        file_id: str,
    ) -> bool:
        result = await db.execute(text(
            "SELECT storage_key FROM files WHERE id = :id AND tenant_id = :tenant_id"
        ), {"id": file_id, "tenant_id": tenant_id})
        row = result.fetchone()

        if not row:
            return False

        await self.storage.delete(row.storage_key)

        await db.execute(text(
            "DELETE FROM files WHERE id = :id AND tenant_id = :tenant_id"
        ), {"id": file_id, "tenant_id": tenant_id})
        await db.commit()

        logger.info("File deleted: id=%s", file_id)
        return True

    async def get_download_url(
        self,
        db: AsyncSession,
        tenant_id: str,
        file_id: str,
        expiry: int = 3600,
    ) -> Optional[str]:
        result = await db.execute(text(
            "SELECT storage_key FROM files WHERE id = :id AND tenant_id = :tenant_id"
        ), {"id": file_id, "tenant_id": tenant_id})
        row = result.fetchone()

        if not row:
            return None

        return await self.storage.get_url(row.storage_key, expiry)


upload_handler = FileUploadHandler()
