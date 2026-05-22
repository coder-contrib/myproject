import os

CORS_ORIGINS: list[str] = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://localhost:5173,http://localhost:8080,http://localhost:8000,http://localhost:52345,http://localhost:52346,http://localhost:52347,http://localhost:52348,http://localhost:52349,http://localhost:52350"
    ).split(",")
    if origin.strip()
]

# In development, allow all origins if DEBUG is set
if os.getenv("DEBUG", "false").lower() == "true" or os.getenv("CORS_ALLOW_ALL", "false").lower() == "true":
    CORS_ORIGINS = ["*"]

CORS_CONFIG = {
    "allow_origins": CORS_ORIGINS,
    "allow_credentials": True if CORS_ORIGINS != ["*"] else False,
    "allow_methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    "allow_headers": [
        "Authorization",
        "Content-Type",
        "Accept",
        "X-Request-ID",
        "X-Tenant-ID",
        "X-Branch-ID",
    ],
    "expose_headers": [
        "X-Request-ID",
        "X-Response-Time",
        "X-RateLimit-Remaining",
        "X-RateLimit-Limit",
    ],
    "max_age": 600,
}
