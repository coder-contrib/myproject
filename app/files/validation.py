import logging
import struct
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field

from app.files.config import file_config

logger = logging.getLogger("files.validation")

# Magic bytes for common file types
MAGIC_BYTES = {
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"\xff\xd8\xff": "image/jpeg",
    b"GIF87a": "image/gif",
    b"GIF89a": "image/gif",
    b"%PDF": "application/pdf",
    b"PK\x03\x04": "application/zip",  # Also docx, xlsx, pptx
    b"PK\x05\x06": "application/zip",
    b"Rar!\x1a\x07": "application/x-rar-compressed",
    b"7z\xbc\xaf\x27\x1c": "application/x-7z-compressed",
    b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1": "application/msword",  # OLE2 (doc, xls, ppt)
}

# Extension to MIME type mapping
EXTENSION_MIME_MAP = {
    ".pdf": "application/pdf",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xls": "application/vnd.ms-excel",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".csv": "text/csv",
    ".txt": "text/plain",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".svg": "image/svg+xml",
    ".zip": "application/zip",
    ".rar": "application/x-rar-compressed",
    ".7z": "application/x-7z-compressed",
    ".json": "application/json",
    ".xml": "application/xml",
}

# Dangerous patterns to reject
DANGEROUS_EXTENSIONS = {
    ".exe", ".bat", ".cmd", ".com", ".msi", ".scr",
    ".ps1", ".vbs", ".js", ".wsh", ".wsf",
    ".sh", ".bash", ".csh",
    ".php", ".asp", ".aspx", ".jsp",
    ".py", ".rb", ".pl",
    ".dll", ".so", ".dylib",
}


@dataclass
class ValidationResult:
    valid: bool
    errors: list[str] = field(default_factory=list)
    detected_mime: Optional[str] = None
    file_size: int = 0


class MimeTypeValidator:
    """Validates file MIME types using magic bytes and extension mapping."""

    def detect_from_bytes(self, data: bytes) -> Optional[str]:
        for magic, mime_type in MAGIC_BYTES.items():
            if data[:len(magic)] == magic:
                return mime_type
        return None

    def detect_from_extension(self, filename: str) -> Optional[str]:
        ext = Path(filename).suffix.lower()
        return EXTENSION_MIME_MAP.get(ext)

    def validate_consistency(
        self,
        filename: str,
        declared_mime: Optional[str],
        data: bytes,
    ) -> tuple[bool, str, Optional[str]]:
        """Check that declared MIME, extension, and actual content are consistent."""
        ext = Path(filename).suffix.lower()
        detected_mime = self.detect_from_bytes(data)
        ext_mime = self.detect_from_extension(filename)

        # If we can detect from bytes, use that as ground truth
        if detected_mime:
            # ZIP-based formats (docx, xlsx) all start with PK
            if detected_mime == "application/zip" and ext in (".docx", ".xlsx", ".pptx"):
                detected_mime = ext_mime
            return True, "", detected_mime

        # For text-based formats where magic bytes don't help
        if ext in (".csv", ".txt", ".json", ".xml", ".svg"):
            if self._looks_like_text(data):
                return True, "", ext_mime
            return False, f"File content does not appear to be text for {ext} file", None

        # For WebP (RIFF....WEBP)
        if ext == ".webp" and len(data) >= 12:
            if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
                return True, "", "image/webp"
            return False, "File content does not match WebP format", None

        # If we can't detect, trust the extension if it's in allowed list
        if ext_mime and ext_mime in file_config.allowed_mime_types:
            return True, "", ext_mime

        return False, f"Unable to verify MIME type for extension {ext}", None

    def _looks_like_text(self, data: bytes) -> bool:
        try:
            sample = data[:8192]
            sample.decode("utf-8")
            return True
        except (UnicodeDecodeError, ValueError):
            # Try latin-1 as fallback for CSV
            try:
                sample = data[:8192]
                sample.decode("latin-1")
                null_ratio = sample.count(b"\x00") / len(sample)
                return null_ratio < 0.01
            except Exception:
                return False


class FileValidator:
    """Validates uploaded files for size, type, extension, and content safety."""

    def __init__(self):
        self.mime_validator = MimeTypeValidator()

    def validate(
        self,
        filename: str,
        data: bytes,
        declared_content_type: Optional[str] = None,
        max_size: Optional[int] = None,
        allowed_extensions: Optional[list[str]] = None,
        allowed_mime_types: Optional[list[str]] = None,
    ) -> ValidationResult:
        errors = []
        max_size = max_size or file_config.max_file_size
        allowed_ext = allowed_extensions or file_config.allowed_extensions
        allowed_mimes = allowed_mime_types or file_config.allowed_mime_types

        # Size validation
        if len(data) > max_size:
            errors.append(
                f"File size {len(data)} bytes exceeds maximum {max_size} bytes"
            )

        if len(data) == 0:
            errors.append("File is empty")
            return ValidationResult(valid=False, errors=errors, file_size=0)

        # Extension validation
        ext = Path(filename).suffix.lower().lstrip(".")
        if not ext:
            errors.append("File has no extension")
        elif ext not in allowed_ext:
            errors.append(f"Extension '.{ext}' is not allowed")

        # Dangerous extension check
        full_ext = Path(filename).suffix.lower()
        if full_ext in DANGEROUS_EXTENSIONS:
            errors.append(f"Extension '{full_ext}' is blocked for security reasons")

        # Double extension check (e.g., file.pdf.exe)
        name_parts = Path(filename).name.split(".")
        if len(name_parts) > 2:
            for part in name_parts[1:]:
                if f".{part.lower()}" in DANGEROUS_EXTENSIONS:
                    errors.append(
                        f"Hidden dangerous extension detected: .{part}"
                    )

        # Filename sanitization
        if any(c in filename for c in ["../", "..\\" , "\x00"]):
            errors.append("Filename contains path traversal characters")

        # MIME type validation
        consistent, mime_error, detected_mime = self.mime_validator.validate_consistency(
            filename, declared_content_type, data
        )
        if not consistent:
            errors.append(mime_error)

        if detected_mime and detected_mime not in allowed_mimes:
            errors.append(f"MIME type '{detected_mime}' is not allowed")

        # Content safety: check for embedded scripts in images/docs
        if detected_mime and detected_mime.startswith("image/"):
            if self._contains_script_injection(data):
                errors.append("File contains potential script injection")

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            detected_mime=detected_mime,
            file_size=len(data),
        )

    def _contains_script_injection(self, data: bytes) -> bool:
        dangerous_patterns = [
            b"<script",
            b"javascript:",
            b"on\x00error",
            b"onerror=",
            b"onload=",
            b"eval(",
        ]
        lower_data = data[:10240].lower()
        return any(pattern in lower_data for pattern in dangerous_patterns)
