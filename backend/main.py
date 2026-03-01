from __future__ import annotations

import json
import logging
import os
import time
from collections import defaultdict, deque
from functools import lru_cache
from importlib import import_module
from importlib.util import find_spec
from pathlib import Path
from threading import Lock
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, ConfigDict, Field

from backend.exercise_grader import ExerciseGrader
from backend.html_views import render_course_index, render_lesson_page
from backend.sql_runner import SqlRunner, SqlValidationError


class ExecuteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lessonId: str = Field(min_length=1, max_length=64, pattern=r"^[a-z0-9\-]+$")
    sql: str = Field(min_length=1, max_length=int(os.getenv("SQL_MAX_QUERY_LENGTH", "5000")))


class ExecuteResponse(BaseModel):
    columns: list[str]
    rows: list[list[object]]
    executionMs: float
    error: str | None
    truncated: bool
    gradingStatus: str
    feedback: str


class ResetDbResponse(BaseModel):
    status: str
    message: str


class LessonSummaryResponse(BaseModel):
    slug: str
    title: str
    level: str
    order: int
    description: str | None = None


class LessonDetailResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    slug: str
    title: str
    level: str
    order: int
    intro: str
    explanation: str
    examples: list[dict[str, str]]
    exercise: str
    solutionHints: list[str]
    expectedQueryPatterns: list[str]
    validation: dict[str, object]
    starterQuery: str


repo_root = Path(__file__).resolve().parents[1]
runtime_dir = Path(os.getenv("SQLITE_RUNTIME_DIR", repo_root / ".runtime/sqlite"))
base_db_path_raw = os.getenv("SQLITE_BASE_DB_PATH")
base_db_path = Path(base_db_path_raw) if base_db_path_raw else None

logger = logging.getLogger(__name__)


class MetricsStore:
    def __init__(self) -> None:
        self._lock = Lock()
        self._request_counter: dict[tuple[str, str, int], int] = defaultdict(int)
        self._status_counter: dict[int, int] = defaultdict(int)
        self._rate_limit_counter: dict[tuple[str, str], int] = defaultdict(int)
        self._histogram_buckets = [0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0]
        self._duration_histogram_buckets: dict[tuple[str, str], list[int]] = defaultdict(
            lambda: [0 for _ in self._histogram_buckets]
        )
        self._duration_histogram_sum: dict[tuple[str, str], float] = defaultdict(float)
        self._duration_histogram_count: dict[tuple[str, str], int] = defaultdict(int)
        self._app_error_counter: dict[str, int] = defaultdict(int)

    def record_request(self, method: str, path: str, status_code: int, duration_s: float) -> None:
        key = (method, path, status_code)
        duration_key = (method, path)
        with self._lock:
            self._request_counter[key] += 1
            self._status_counter[status_code] += 1
            if status_code == 429:
                self._rate_limit_counter[duration_key] += 1
            self._duration_histogram_count[duration_key] += 1
            self._duration_histogram_sum[duration_key] += duration_s
            for idx, bucket in enumerate(self._histogram_buckets):
                if duration_s <= bucket:
                    self._duration_histogram_buckets[duration_key][idx] += 1

    def record_error(self, error_type: str) -> None:
        with self._lock:
            self._app_error_counter[error_type] += 1

    @staticmethod
    def _labels(labels: dict[str, str | int | float]) -> str:
        escaped = []
        for key, value in labels.items():
            raw = str(value).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
            escaped.append(f'{key}="{raw}"')
        return "{" + ",".join(escaped) + "}"

    def render_prometheus(self) -> str:
        lines = [
            "# HELP sql_course_http_requests_total Total liczba żądań HTTP.",
            "# TYPE sql_course_http_requests_total counter",
        ]
        with self._lock:
            request_items = sorted(self._request_counter.items())
            status_items = sorted(self._status_counter.items())
            rate_limit_items = sorted(self._rate_limit_counter.items())
            duration_items = sorted(self._duration_histogram_count.items())
            error_items = sorted(self._app_error_counter.items())

        for (method, path, status), value in request_items:
            labels = self._labels({"method": method, "path": path, "status": status})
            lines.append(f"sql_course_http_requests_total{labels} {value}")

        lines.extend(
            [
                "# HELP sql_course_http_status_total Total odpowiedzi HTTP według statusu.",
                "# TYPE sql_course_http_status_total counter",
            ]
        )
        for status, value in status_items:
            labels = self._labels({"status": status})
            lines.append(f"sql_course_http_status_total{labels} {value}")

        lines.extend(
            [
                "# HELP sql_course_http_429_total Total odpowiedzi 429 (rate limit).",
                "# TYPE sql_course_http_429_total counter",
            ]
        )
        for (method, path), value in rate_limit_items:
            labels = self._labels({"method": method, "path": path})
            lines.append(f"sql_course_http_429_total{labels} {value}")

        lines.extend(
            [
                "# HELP sql_course_http_request_duration_seconds Czas obsługi żądań HTTP.",
                "# TYPE sql_course_http_request_duration_seconds histogram",
            ]
        )
        with self._lock:
            buckets_map = dict(self._duration_histogram_buckets)
            sums_map = dict(self._duration_histogram_sum)
            counts_map = dict(self._duration_histogram_count)
        for (method, path), count in duration_items:
            buckets = buckets_map[(method, path)]
            cumulative = 0
            for idx, bucket in enumerate(self._histogram_buckets):
                cumulative += buckets[idx]
                labels = self._labels({"method": method, "path": path, "le": bucket})
                lines.append(f"sql_course_http_request_duration_seconds_bucket{labels} {cumulative}")
            inf_labels = self._labels({"method": method, "path": path, "le": "+Inf"})
            lines.append(f"sql_course_http_request_duration_seconds_bucket{inf_labels} {count}")
            labels = self._labels({"method": method, "path": path})
            lines.append(
                f"sql_course_http_request_duration_seconds_sum{labels} {sums_map[(method, path)]:.6f}"
            )
            lines.append(f"sql_course_http_request_duration_seconds_count{labels} {counts_map[(method, path)]}")

        lines.extend(
            [
                "# HELP sql_course_app_errors_total Total błędów aplikacyjnych przekazanych do eksportera.",
                "# TYPE sql_course_app_errors_total counter",
            ]
        )
        for error_type, value in error_items:
            labels = self._labels({"type": error_type})
            lines.append(f"sql_course_app_errors_total{labels} {value}")

        return "\n".join(lines) + "\n"


class ErrorReporter:
    def __init__(self) -> None:
        self._capture_exception: Any | None = None
        self._capture_message: Any | None = None
        self._push_scope: Any | None = None
        self._enabled = False
        self._backend = os.getenv("ERROR_REPORTING_BACKEND", "sentry").lower()

        if self._backend != "sentry":
            logger.info("Pomijam inicjalizację reportera błędów: ERROR_REPORTING_BACKEND=%s", self._backend)
            return

        sentry_dsn = os.getenv("SENTRY_DSN")
        if not sentry_dsn:
            logger.info("SENTRY_DSN nie ustawione: reporter błędów działa tylko w logach.")
            return
        if find_spec("sentry_sdk") is None:
            logger.warning("Brak pakietu sentry_sdk, nie można włączyć eksportu błędów.")
            return

        sentry_sdk = import_module("sentry_sdk")
        integrations = []
        fastapi_integration_cls: Any | None = None
        if find_spec("sentry_sdk.integrations.fastapi") is not None:
            fastapi_integration_cls = import_module("sentry_sdk.integrations.fastapi").FastApiIntegration
        if fastapi_integration_cls is not None:
            integrations.append(fastapi_integration_cls())

        sentry_sdk.init(
            dsn=sentry_dsn,
            integrations=integrations,
            traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.0")),
        )
        self._capture_exception = sentry_sdk.capture_exception
        self._capture_message = sentry_sdk.capture_message
        self._push_scope = sentry_sdk.push_scope
        self._enabled = True
        logger.info("Włączono eksport błędów do Sentry.")

    def capture_exception(self, exc: Exception, *, tags: dict[str, str] | None = None) -> None:
        if not self._enabled or self._capture_exception is None:
            return
        if tags and self._push_scope is not None:
            with self._push_scope() as scope:
                for key, value in tags.items():
                    scope.set_tag(key, value)
                self._capture_exception(exc)
            return
        self._capture_exception(exc)

    def capture_sql_error(self, message: str, *, lesson_id: str, client_ip: str) -> None:
        if not self._enabled or self._capture_message is None:
            return
        if self._push_scope is not None:
            with self._push_scope() as scope:
                scope.set_tag("source", "sql_runner")
                scope.set_tag("lesson_id", lesson_id)
                scope.set_tag("client_ip", client_ip)
                self._capture_message(message, level="error")
            return
        self._capture_message(message, level="error")


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

runner = SqlRunner(
    schema_path=repo_root / "db/schema.sql",
    seed_path=repo_root / "db/seed.sql",
    runtime_dir=runtime_dir,
    base_db_path=base_db_path,
    query_timeout_s=float(os.getenv("SQL_QUERY_TIMEOUT_S", "3")),
    max_rows=int(os.getenv("SQL_MAX_ROWS", "200")),
    max_cell_bytes=int(os.getenv("SQL_MAX_CELL_BYTES", "100000")),
    max_output_bytes=int(os.getenv("SQL_MAX_OUTPUT_BYTES", "1000000")),
)
grader = ExerciseGrader(lessons_dir=repo_root / "content/sql-course", runner=runner)
rate_limiter = InMemoryRateLimiter(
    max_requests=int(os.getenv("EXECUTE_RATE_LIMIT_MAX_REQUESTS", "20")),
    window_s=float(os.getenv("EXECUTE_RATE_LIMIT_WINDOW_S", "60")),
)

app = FastAPI()
metrics_store = MetricsStore()
error_reporter = ErrorReporter()


@app.middleware("http")
async def prometheus_metrics_middleware(request: Request, call_next: Any) -> Any:
    started = time.monotonic()
    path = request.url.path
    method = request.method
    try:
        response = await call_next(request)
    except Exception as exc:
        duration_s = time.monotonic() - started
        metrics_store.record_request(method=method, path=path, status_code=500, duration_s=duration_s)
        metrics_store.record_error("unhandled_exception")
        error_reporter.capture_exception(exc, tags={"path": path, "method": method})
        raise

    duration_s = time.monotonic() - started
    metrics_store.record_request(
        method=method,
        path=path,
        status_code=response.status_code,
        duration_s=duration_s,
    )
    return response


@lru_cache(maxsize=1)
def load_lessons() -> list[dict[str, object]]:
    lessons_dir = repo_root / "content/sql-course"
    lessons: list[dict[str, object]] = []

    for lesson_file in lessons_dir.glob("*.json"):
        lesson = json.loads(lesson_file.read_text(encoding="utf-8"))
        lessons.append(lesson)

    lessons.sort(key=lambda lesson: int(lesson["order"]))
    return lessons


def get_lesson_by_slug(slug: str) -> dict[str, object]:
    lessons = load_lessons()
    lessons_by_slug = {str(lesson["slug"]): lesson for lesson in lessons}

    if not slug or slug not in lessons_by_slug:
        raise HTTPException(status_code=404, detail="Nie znaleziono lekcji o podanym slug")

    return lessons_by_slug[slug]


@app.get("/lessons", response_model=list[LessonSummaryResponse])
def get_lessons() -> list[LessonSummaryResponse]:
    lessons = load_lessons()
    return [
        LessonSummaryResponse(
            slug=str(lesson["slug"]),
            title=str(lesson["title"]),
            level=str(lesson["level"]),
            order=int(lesson["order"]),
            description=str(lesson.get("intro")) if lesson.get("intro") is not None else None,
        )
        for lesson in lessons
    ]


@app.get("/lessons/{slug}", response_model=LessonDetailResponse)
def get_lesson(slug: str) -> LessonDetailResponse:
    lesson = get_lesson_by_slug(slug)
    return LessonDetailResponse.model_validate(lesson)


@app.get("/kurs/sql", response_class=HTMLResponse)
@app.get("/kurs/sql/", response_class=HTMLResponse)
def sql_course_index() -> HTMLResponse:
    html = render_course_index(load_lessons())
    return HTMLResponse(content=html)


@app.get("/kurs/sql/{slug}", response_class=HTMLResponse)
def sql_course_lesson(slug: str) -> HTMLResponse:
    lessons = load_lessons()
    index_by_slug = {str(lesson["slug"]): idx for idx, lesson in enumerate(lessons)}

    if not slug:
        raise HTTPException(status_code=404, detail="Brak slug lekcji")
    if slug not in index_by_slug:
        raise HTTPException(status_code=404, detail="Nie znaleziono lekcji o podanym slug")

    lesson_index = index_by_slug[slug]
    lesson = lessons[lesson_index]

    prev_lesson = lessons[lesson_index - 1] if lesson_index > 0 else None
    next_lesson = lessons[lesson_index + 1] if lesson_index < len(lessons) - 1 else None

    html = render_lesson_page(
        lesson=lesson,
        prev_lesson=prev_lesson,
        next_lesson=next_lesson,
    )
    return HTMLResponse(content=html)


@app.post("/execute", response_model=ExecuteResponse)
def execute(request: ExecuteRequest, http_request: Request) -> ExecuteResponse:
    client = http_request.client
    client_ip = client.host if client else "unknown"
    if not rate_limiter.allow(client_ip):
        raise HTTPException(status_code=429, detail="Przekroczono limit żądań. Spróbuj ponownie później.")

    try:
        result = runner.execute(lesson_id=request.lessonId, sql=request.sql)
        grade_result = grader.grade(lesson_id=request.lessonId, sql=request.sql, actual=result)

        safe_error = result.error
        if result.error is not None:
            logger.error(
                "Błąd wykonania zapytania SQL dla lessonId=%s i client=%s: %s",
                request.lessonId,
                client_ip,
                result.error,
            )
            metrics_store.record_error("sql_execution_error")
            error_reporter.capture_sql_error(
                result.error,
                lesson_id=request.lessonId,
                client_ip=client_ip,
            )

        return ExecuteResponse(
            columns=result.columns,
            rows=result.rows,
            executionMs=round(result.execution_ms, 3),
            error=safe_error,
            truncated=result.truncated,
            gradingStatus=grade_result.status,
            feedback=grade_result.feedback,
        )
    except SqlValidationError as exc:
        metrics_store.record_error("sql_validation_error")
        return ExecuteResponse(
            columns=[],
            rows=[],
            executionMs=0.0,
            error=str(exc),
            truncated=False,
            gradingStatus="fail",
            feedback=f"❌ Zapytanie nie przeszło walidacji: {exc}",
        )
    except Exception as exc:
        logger.exception("Nieoczekiwany błąd endpointu /execute dla client=%s", client_ip)
        metrics_store.record_error("execute_exception")
        error_reporter.capture_exception(
            exc,
            tags={"endpoint": "/execute", "client_ip": client_ip},
        )
        return ExecuteResponse(
            columns=[],
            rows=[],
            executionMs=0.0,
            error="Wystąpił nieoczekiwany błąd po stronie serwera.",
            truncated=False,
            gradingStatus="fail",
            feedback="❌ Nie udało się wykonać zapytania. Spróbuj ponownie później.",
        )


@app.post("/reset-db", response_model=ResetDbResponse)
def reset_db() -> ResetDbResponse:
    runner.reset_base_snapshot()
    return ResetDbResponse(status="ok", message="Stan bazy został zresetowany.")


@app.get("/metrics")
def prometheus_metrics() -> HTMLResponse:
    return HTMLResponse(content=metrics_store.render_prometheus(), media_type="text/plain; version=0.0.4")
