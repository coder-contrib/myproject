import os

CORS_ORIGINS: list[str] = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
    if origin.strip()
]

CORS_CONFIG = {
    "allow_origins": CORS_ORIGINS,
    "allow_credentials": True,
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
