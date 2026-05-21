import re
import html
from typing import Any

_SQL_PATTERNS = re.compile(
    r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|EXEC|UNION|TRUNCATE|GRANT|REVOKE)\b"
    r"|--|;\s*$|/\*|\*/|xp_|sp_|0x[0-9a-fA-F]+)",
    re.IGNORECASE,
)

_XSS_PATTERNS = re.compile(
    r"(<\s*script|javascript\s*:|on\w+\s*=|<\s*iframe|<\s*object|<\s*embed|<\s*form)",
    re.IGNORECASE,
)

_NULL_BYTE = re.compile(r"\x00")


def sanitize_input(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, str):
        value = _NULL_BYTE.sub("", value)
        value = value.strip()
        if len(value) > 10000:
            value = value[:10000]
        return value
    if isinstance(value, dict):
        return {k: sanitize_input(v) for k, v in value.items()}
    if isinstance(value, list):
        return [sanitize_input(v) for v in value]
    return value


def sanitize_html(value: str) -> str:
    if not value:
        return value
    return html.escape(value, quote=True)


def strip_sql_injection(value: str) -> str:
    if not value:
        return value
    return _SQL_PATTERNS.sub("", value)


def contains_xss(value: str) -> bool:
    if not value:
        return False
    return bool(_XSS_PATTERNS.search(value))


def contains_sql_injection(value: str) -> bool:
    if not value:
        return False
    return bool(_SQL_PATTERNS.search(value))
