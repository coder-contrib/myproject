import time
from collections import defaultdict
from dataclasses import dataclass, field
from fastapi import Request, HTTPException, status


@dataclass
class _BucketEntry:
    tokens: float
    last_refill: float


class RateLimiter:
    def __init__(
        self,
        requests_per_minute: int = 60,
        burst_size: int = 10,
    ):
        self.rate = requests_per_minute / 60.0
        self.burst_size = burst_size
        self._buckets: dict[str, _BucketEntry] = defaultdict(
            lambda: _BucketEntry(tokens=burst_size, last_refill=time.monotonic())
        )

    def _get_key(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"

        user_id = getattr(request.state, "user_id", None)
        if user_id:
            return f"user:{user_id}"
        return f"ip:{ip}"

    def _refill(self, bucket: _BucketEntry) -> None:
        now = time.monotonic()
        elapsed = now - bucket.last_refill
        bucket.tokens = min(self.burst_size, bucket.tokens + elapsed * self.rate)
        bucket.last_refill = now

    def check(self, request: Request) -> None:
        key = self._get_key(request)
        bucket = self._buckets[key]
        self._refill(bucket)

        if bucket.tokens < 1:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please slow down.",
                headers={"Retry-After": str(int(1 / self.rate))},
            )
        bucket.tokens -= 1

    def get_remaining(self, request: Request) -> int:
        key = self._get_key(request)
        bucket = self._buckets[key]
        self._refill(bucket)
        return max(0, int(bucket.tokens))


_default_limiter = RateLimiter(requests_per_minute=60, burst_size=10)
_auth_limiter = RateLimiter(requests_per_minute=10, burst_size=5)


def get_rate_limiter(endpoint_type: str = "default") -> RateLimiter:
    if endpoint_type == "auth":
        return _auth_limiter
    return _default_limiter
