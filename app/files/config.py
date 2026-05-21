import os
from dataclasses import dataclass, field


@dataclass
class FileConfig:
    storage_provider: str = os.getenv("FILE_STORAGE_PROVIDER", "local")
    local_storage_path: str = os.getenv("FILE_LOCAL_PATH", "./uploads")
    s3_endpoint_url: str = os.getenv("FILE_S3_ENDPOINT", "")
    s3_access_key: str = os.getenv("FILE_S3_ACCESS_KEY", "")
    s3_secret_key: str = os.getenv("FILE_S3_SECRET_KEY", "")
    s3_bucket: str = os.getenv("FILE_S3_BUCKET", "erp-files")
    s3_region: str = os.getenv("FILE_S3_REGION", "us-east-1")
    s3_presigned_expiry: int = int(os.getenv("FILE_S3_PRESIGNED_EXPIRY", "3600"))
    max_file_size: int = int(os.getenv("FILE_MAX_SIZE", str(50 * 1024 * 1024)))  # 50MB
    max_files_per_upload: int = int(os.getenv("FILE_MAX_PER_UPLOAD", "10"))
    allowed_extensions: list[str] = field(default_factory=lambda: [
        "pdf", "doc", "docx", "xls", "xlsx", "csv", "txt",
        "png", "jpg", "jpeg", "gif", "webp", "svg",
        "zip", "rar", "7z",
        "json", "xml",
    ])
    allowed_mime_types: list[str] = field(default_factory=lambda: [
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "text/csv",
        "text/plain",
        "image/png",
        "image/jpeg",
        "image/gif",
        "image/webp",
        "image/svg+xml",
        "application/zip",
        "application/x-rar-compressed",
        "application/x-7z-compressed",
        "application/json",
        "application/xml",
        "text/xml",
    ])


file_config = FileConfig()
