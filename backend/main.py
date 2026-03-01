from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from backend.exercise_grader import ExerciseGrader
from backend.html_views import render_course_index, render_lesson_page
from backend.sql_runner import SqlRunner, SqlValidationError


class ExecuteRequest(BaseModel):
    lessonId: str = Field(min_length=1)
    sql: str = Field(min_length=1)


class ExecuteResponse(BaseModel):
    columns: list[str]
    rows: list[list[object]]
    executionMs: float
    error: str | None
    truncated: bool
    gradingStatus: str
    feedback: str


repo_root = Path(__file__).resolve().parents[1]
runtime_dir = Path(os.getenv("SQLITE_RUNTIME_DIR", repo_root / ".runtime/sqlite"))
base_db_path_raw = os.getenv("SQLITE_BASE_DB_PATH")
base_db_path = Path(base_db_path_raw) if base_db_path_raw else None

runner = SqlRunner(
    schema_path=repo_root / "db/schema.sql",
    seed_path=repo_root / "db/seed.sql",
    runtime_dir=runtime_dir,
    base_db_path=base_db_path,
    query_timeout_s=float(os.getenv("SQL_QUERY_TIMEOUT_S", "3")),
    max_rows=int(os.getenv("SQL_MAX_ROWS", "200")),
)
grader = ExerciseGrader(lessons_dir=repo_root / "content/sql-course", runner=runner)

app = FastAPI()


@lru_cache(maxsize=1)
def load_lessons() -> list[dict[str, object]]:
    lessons_dir = repo_root / "content/sql-course"
    lessons: list[dict[str, object]] = []

    for lesson_file in lessons_dir.glob("*.json"):
        lesson = json.loads(lesson_file.read_text(encoding="utf-8"))
        lessons.append(lesson)

    lessons.sort(key=lambda lesson: int(lesson["order"]))
    return lessons


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
def execute(request: ExecuteRequest) -> ExecuteResponse:
    try:
        result = runner.execute(lesson_id=request.lessonId, sql=request.sql)
        grade_result = grader.grade(lesson_id=request.lessonId, sql=request.sql, actual=result)
        return ExecuteResponse(
            columns=result.columns,
            rows=result.rows,
            executionMs=round(result.execution_ms, 3),
            error=result.error,
            truncated=result.truncated,
            gradingStatus=grade_result.status,
            feedback=grade_result.feedback,
        )
    except SqlValidationError as exc:
        return ExecuteResponse(
            columns=[],
            rows=[],
            executionMs=0.0,
            error=str(exc),
            truncated=False,
            gradingStatus="fail",
            feedback=f"❌ Zapytanie nie przeszło walidacji: {exc}",
        )
