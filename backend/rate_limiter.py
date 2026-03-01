from __future__ import annotations

import logging
import os
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from threading import Lock
from typing import Protocol

from fastapi import Request

logger = logging.getLogger(__name__)


class RateLimiter(Protocol):
    def allow(self, key: str) -> bool:
        """Zwraca True, jeżeli żądanie dla podanego klucza może zostać obsłużone."""


class InMemoryRateLimiter:
    def __init__(self, max_requests: int, window_s: float) -> None:
        self.max_requests = max_requests
        self.window_s = window_s
        self._entries: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        with self._lock:
            bucket = self._entries[key]
            while bucket and now - bucket[0] > self.window_s:
                bucket.popleft()

            if len(bucket) >= self.max_requests:
                return False

            bucket.append(now)
            return True


class RedisRateLimiter:
    """Sliding window limiter oparty o Redis sorted set."""

    def __init__(
        self,
        redis_client: object,
        *,
        max_requests: int,
        window_s: float,
        key_prefix: str = "rate_limit",
    ) -> None:
        self._redis = redis_client
        self.max_requests = max_requests
        self.window_s = window_s
        self.key_prefix = key_prefix

    def allow(self, key: str) -> bool:
        now_ms = int(time.time() * 1000)
        window_ms = int(self.window_s * 1000)
        window_start = now_ms - window_ms
        redis_key = f"{self.key_prefix}:{key}"
        member = f"{now_ms}-{time.monotonic_ns()}"

        pipeline = self._redis.pipeline(transaction=True)
        pipeline.zremrangebyscore(redis_key, 0, window_start)
        pipeline.zcard(redis_key)
        pipeline.expire(redis_key, max(1, int(self.window_s) + 1))
        _, current_count, _ = pipeline.execute()

        if int(current_count) >= self.max_requests:
            return False

        pipeline = self._redis.pipeline(transaction=True)
        pipeline.zadd(redis_key, {member: now_ms})
        pipeline.expire(redis_key, max(1, int(self.window_s) + 1))
        pipeline.execute()
        return True


@dataclass(frozen=True)
class RateLimitKeyBuilder:
    include_ip: bool = True
    include_session: bool = False
    include_user: bool = False
    session_header: str = "X-Session-Id"
    user_header: str = "X-User-Id"

    def build(self, request: Request) -> str:
        parts: list[str] = []
        if self.include_ip:
            client = request.client
            ip = client.host if client else "unknown"
            parts.append(f"ip:{ip}")

        if self.include_session:
            session_value = request.headers.get(self.session_header)
            if session_value:
                parts.append(f"session:{session_value}")

        if self.include_user:
            user_value = request.headers.get(self.user_header)
            if user_value:
                parts.append(f"user:{user_value}")

        if not parts:
            return "global"

        return "|".join(parts)


@dataclass(frozen=True)
class RateLimiterSettings:
    max_requests: int
    window_s: float
    backend: str
    redis_url: str
    redis_prefix: str


def load_rate_limiter_settings() -> RateLimiterSettings:
    app_env = os.getenv("APP_ENV", "development").lower()
    backend = os.getenv("EXECUTE_RATE_LIMIT_BACKEND")
    selected_backend = backend.lower() if backend else ("redis" if app_env == "production" else "memory")
    return RateLimiterSettings(
        max_requests=int(os.getenv("EXECUTE_RATE_LIMIT_MAX_REQUESTS", "20")),
        window_s=float(os.getenv("EXECUTE_RATE_LIMIT_WINDOW_S", "60")),
        backend=selected_backend,
        redis_url=os.getenv("EXECUTE_RATE_LIMIT_REDIS_URL", "redis://localhost:6379/0"),
        redis_prefix=os.getenv("EXECUTE_RATE_LIMIT_REDIS_PREFIX", "execute"),
    )


def load_rate_limit_key_builder_from_env() -> RateLimitKeyBuilder:
    def _env_bool(name: str, default: bool) -> bool:
        raw = os.getenv(name)
        if raw is None:
            return default
        return raw.strip().lower() in {"1", "true", "yes", "on"}

    return RateLimitKeyBuilder(
        include_ip=_env_bool("EXECUTE_RATE_LIMIT_INCLUDE_IP", True),
        include_session=_env_bool("EXECUTE_RATE_LIMIT_INCLUDE_SESSION", False),
        include_user=_env_bool("EXECUTE_RATE_LIMIT_INCLUDE_USER", False),
        session_header=os.getenv("EXECUTE_RATE_LIMIT_SESSION_HEADER", "X-Session-Id"),
        user_header=os.getenv("EXECUTE_RATE_LIMIT_USER_HEADER", "X-User-Id"),
    )


def create_rate_limiter(settings: RateLimiterSettings) -> RateLimiter:
    if settings.backend == "redis":
        try:
            import redis

            redis_client = redis.Redis.from_url(settings.redis_url)
            redis_client.ping()
            logger.info("Używam RedisRateLimiter (%s)", settings.redis_url)
            return RedisRateLimiter(
                redis_client,
                max_requests=settings.max_requests,
                window_s=settings.window_s,
                key_prefix=settings.redis_prefix,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Nie udało się uruchomić RedisRateLimiter (%s). Fallback do in-memory.", exc)

    return InMemoryRateLimiter(max_requests=settings.max_requests, window_s=settings.window_s)
