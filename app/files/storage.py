import os
import uuid
import logging
import asyncio
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, BinaryIO
from dataclasses import dataclass

from app.files.config import file_config

logger = logging.getLogger("files.storage")


@dataclass
class StoredFile:
    key: str
    size: int
    content_type: str
    etag: Optional[str] = None
    url: Optional[str] = None


class StorageProvider(ABC):
    """Abstract base class for file storage providers."""

    @abstractmethod
    async def upload(self, key: str, data: bytes, content_type: str) -> StoredFile:
        ...

    @abstractmethod
    async def download(self, key: str) -> bytes:
        ...

    @abstractmethod
    async def delete(self, key: str) -> bool:
        ...

    @abstractmethod
    async def exists(self, key: str) -> bool:
        ...

    @abstractmethod
    async def get_url(self, key: str, expiry: int = 3600) -> str:
        ...

    @abstractmethod
    async def get_metadata(self, key: str) -> dict:
        ...

    def generate_key(self, tenant_id: str, filename: str, prefix: str = "") -> str:
        ext = Path(filename).suffix.lower()
        unique_id = uuid.uuid4().hex
        parts = [tenant_id]
        if prefix:
            parts.append(prefix)
        parts.append(f"{unique_id}{ext}")
        return "/".join(parts)


class LocalStorage(StorageProvider):
    """Local filesystem storage provider."""

    def __init__(self, base_path: Optional[str] = None):
        self.base_path = Path(base_path or file_config.local_storage_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def upload(self, key: str, data: bytes, content_type: str) -> StoredFile:
        file_path = self.base_path / key
        file_path.parent.mkdir(parents=True, exist_ok=True)

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, file_path.write_bytes, data)

        import hashlib
        etag = hashlib.md5(data).hexdigest()

        logger.info("File uploaded locally: %s (%d bytes)", key, len(data))
        return StoredFile(
            key=key,
            size=len(data),
            content_type=content_type,
            etag=etag,
        )

    async def download(self, key: str) -> bytes:
        file_path = self.base_path / key
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {key}")

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, file_path.read_bytes)

    async def delete(self, key: str) -> bool:
        file_path = self.base_path / key
        if file_path.exists():
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, file_path.unlink)
            logger.info("File deleted: %s", key)
            return True
        return False

    async def exists(self, key: str) -> bool:
        file_path = self.base_path / key
        return file_path.exists()

    async def get_url(self, key: str, expiry: int = 3600) -> str:
        return f"/files/download/{key}"

    async def get_metadata(self, key: str) -> dict:
        file_path = self.base_path / key
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {key}")
        stat = file_path.stat()
        return {
            "key": key,
            "size": stat.st_size,
            "modified": stat.st_mtime,
        }


class S3Storage(StorageProvider):
    """S3-compatible storage provider (AWS S3, MinIO, DigitalOcean Spaces, etc.)."""

    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None:
            import boto3
            from botocore.config import Config

            kwargs = {
                "service_name": "s3",
                "aws_access_key_id": file_config.s3_access_key,
                "aws_secret_access_key": file_config.s3_secret_key,
                "region_name": file_config.s3_region,
                "config": Config(signature_version="s3v4"),
            }
            if file_config.s3_endpoint_url:
                kwargs["endpoint_url"] = file_config.s3_endpoint_url

            self._client = boto3.client(**kwargs)
        return self._client

    async def upload(self, key: str, data: bytes, content_type: str) -> StoredFile:
        loop = asyncio.get_event_loop()

        def _upload():
            self.client.put_object(
                Bucket=file_config.s3_bucket,
                Key=key,
                Body=data,
                ContentType=content_type,
            )

        await loop.run_in_executor(None, _upload)

        import hashlib
        etag = hashlib.md5(data).hexdigest()

        logger.info("File uploaded to S3: %s (%d bytes)", key, len(data))
        return StoredFile(
            key=key,
            size=len(data),
            content_type=content_type,
            etag=etag,
        )

    async def download(self, key: str) -> bytes:
        loop = asyncio.get_event_loop()

        def _download():
            response = self.client.get_object(
                Bucket=file_config.s3_bucket,
                Key=key,
            )
            return response["Body"].read()

        return await loop.run_in_executor(None, _download)

    async def delete(self, key: str) -> bool:
        loop = asyncio.get_event_loop()

        def _delete():
            self.client.delete_object(
                Bucket=file_config.s3_bucket,
                Key=key,
            )

        await loop.run_in_executor(None, _delete)
        logger.info("File deleted from S3: %s", key)
        return True

    async def exists(self, key: str) -> bool:
        loop = asyncio.get_event_loop()

        def _head():
            try:
                self.client.head_object(
                    Bucket=file_config.s3_bucket,
                    Key=key,
                )
                return True
            except self.client.exceptions.NoSuchKey:
                return False
            except Exception:
                return False

        return await loop.run_in_executor(None, _head)

    async def get_url(self, key: str, expiry: int = 3600) -> str:
        loop = asyncio.get_event_loop()

        def _presign():
            return self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": file_config.s3_bucket, "Key": key},
                ExpiresIn=expiry or file_config.s3_presigned_expiry,
            )

        return await loop.run_in_executor(None, _presign)

    async def get_metadata(self, key: str) -> dict:
        loop = asyncio.get_event_loop()

        def _head():
            return self.client.head_object(
                Bucket=file_config.s3_bucket,
                Key=key,
            )

        response = await loop.run_in_executor(None, _head)
        return {
            "key": key,
            "size": response["ContentLength"],
            "content_type": response["ContentType"],
            "etag": response.get("ETag", "").strip('"'),
            "last_modified": str(response.get("LastModified", "")),
        }


def get_storage() -> StorageProvider:
    provider = file_config.storage_provider.lower()
    if provider == "s3":
        return S3Storage()
    return LocalStorage()
