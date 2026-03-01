from __future__ import annotations

import time
from collections import defaultdict

from fastapi.testclient import TestClient

from backend import main
from backend.rate_limiter import RateLimitKeyBuilder, RedisRateLimiter


class FakePipeline:
    def __init__(self, redis_client: "FakeRedis") -> None:
        self.redis_client = redis_client
        self.commands: list[tuple[str, tuple[object, ...]]] = []

    def zremrangebyscore(self, key: str, min_score: int, max_score: int) -> "FakePipeline":
        self.commands.append(("zremrangebyscore", (key, min_score, max_score)))
        return self

    def zcard(self, key: str) -> "FakePipeline":
        self.commands.append(("zcard", (key,)))
        return self

    def expire(self, key: str, seconds: int) -> "FakePipeline":
        self.commands.append(("expire", (key, seconds)))
        return self

    def zadd(self, key: str, mapping: dict[str, int]) -> "FakePipeline":
        self.commands.append(("zadd", (key, mapping)))
        return self

    def execute(self) -> list[object]:
        results: list[object] = []
        for command, args in self.commands:
            if command == "zremrangebyscore":
                key, _min_score, max_score = args
                before = len(self.redis_client.zsets[key])
                self.redis_client.zsets[key] = {
                    member: score
                    for member, score in self.redis_client.zsets[key].items()
                    if score > max_score
                }
                results.append(before - len(self.redis_client.zsets[key]))
            elif command == "zcard":
                (key,) = args
                results.append(len(self.redis_client.zsets[key]))
            elif command == "expire":
                results.append(True)
            elif command == "zadd":
                key, mapping = args
                self.redis_client.zsets[key].update(mapping)
                results.append(len(mapping))
            else:
                raise ValueError(f"Unsupported command in fake redis pipeline: {command}")
        self.commands = []
        return results


class FakeRedis:
    def __init__(self) -> None:
        self.zsets: dict[str, dict[str, int]] = defaultdict(dict)

    def pipeline(self, transaction: bool = True) -> FakePipeline:  # noqa: ARG002
        return FakePipeline(self)


client = TestClient(main.app)


def _execute_sql(headers: dict[str, str] | None = None) -> int:
    response = client.post(
        "/execute",
        json={"lessonId": "01-select-basics", "sql": "SELECT 1 AS ok"},
        headers=headers,
    )
    return response.status_code


def test_execute_rate_limit_redis_blocks_after_limit(monkeypatch) -> None:
    limiter = RedisRateLimiter(FakeRedis(), max_requests=2, window_s=60, key_prefix="test")
    monkeypatch.setattr(main, "rate_limiter", limiter)
    monkeypatch.setattr(
        main,
        "rate_limit_key_builder",
        RateLimitKeyBuilder(include_ip=True, include_session=False, include_user=False),
    )

    assert _execute_sql() == 200
    assert _execute_sql() == 200
    assert _execute_sql() == 429


def test_execute_rate_limit_redis_tracks_session_key(monkeypatch) -> None:
    limiter = RedisRateLimiter(FakeRedis(), max_requests=1, window_s=60, key_prefix="test")
    monkeypatch.setattr(main, "rate_limiter", limiter)
    monkeypatch.setattr(
        main,
        "rate_limit_key_builder",
        RateLimitKeyBuilder(include_ip=True, include_session=True, include_user=False),
    )

    assert _execute_sql(headers={"X-Session-Id": "alpha"}) == 200
    assert _execute_sql(headers={"X-Session-Id": "alpha"}) == 429
    assert _execute_sql(headers={"X-Session-Id": "beta"}) == 200


def test_redis_rate_limiter_allows_again_after_window() -> None:
    limiter = RedisRateLimiter(FakeRedis(), max_requests=1, window_s=0.05, key_prefix="test")

    assert limiter.allow("ip:127.0.0.1") is True
    assert limiter.allow("ip:127.0.0.1") is False

    time.sleep(0.06)

    assert limiter.allow("ip:127.0.0.1") is True
