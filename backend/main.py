from __future__ import annotations

import json
import os
from functools import lru_cache
from html import escape
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from backend.exercise_grader import ExerciseGrader
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


def render_layout(content: str, title: str) -> str:
    return f"""
<!doctype html>
<html lang="pl">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{escape(title)}</title>
    <style>
      body {{ font-family: Arial, sans-serif; margin: 2rem auto; max-width: 860px; line-height: 1.5; padding: 0 1rem; }}
      h1, h2 {{ margin-bottom: 0.5rem; }}
      ul {{ padding-left: 1.2rem; }}
      .nav {{ display: flex; gap: 0.75rem; flex-wrap: wrap; margin-top: 2rem; }}
      .btn {{ border: 1px solid #ccc; border-radius: 6px; padding: 0.5rem 0.75rem; text-decoration: none; color: #222; }}
      .btn.disabled {{ color: #999; border-color: #e2e2e2; pointer-events: none; }}
      pre {{ background: #f4f4f4; padding: 0.75rem; border-radius: 6px; overflow-x: auto; }}
      .muted {{ color: #666; }}
    </style>
  </head>
  <body>
    {content}
  </body>
</html>
""".strip()


@app.get("/kurs/sql", response_class=HTMLResponse)
@app.get("/kurs/sql/", response_class=HTMLResponse)
def sql_course_index() -> HTMLResponse:
    lesson_items = "\n".join(
        (
            f"<li><a href='/kurs/sql/{escape(str(lesson['slug']))}'>{escape(str(lesson['title']))}</a> "
            f"<span class='muted'>(#{lesson['order']})</span></li>"
        )
        for lesson in load_lessons()
    )

    html = render_layout(
        f"""
        <h1>Kurs SQL – spis lekcji</h1>
        <ul>{lesson_items}</ul>
        """,
        title="Kurs SQL – spis lekcji",
    )
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

    examples_html = "".join(
        f"<li><p>{escape(str(example['description']))}</p><pre>{escape(str(example['query']))}</pre></li>"
        for example in lesson["examples"]
    )

    prev_button = (
        f"<a class='btn' href='/kurs/sql/{escape(str(prev_lesson['slug']))}'>Poprzednie ćwiczenie</a>"
        if prev_lesson
        else "<span class='btn disabled'>Poprzednie ćwiczenie</span>"
    )
    next_button = (
        f"<a class='btn' href='/kurs/sql/{escape(str(next_lesson['slug']))}'>Następne ćwiczenie</a>"
        if next_lesson
        else "<span class='btn disabled'>Następne ćwiczenie</span>"
    )

    html = render_layout(
        f"""
        <h1>{escape(str(lesson['title']))}</h1>
        <p class='muted'>Lekcja #{lesson['order']}</p>

        <section>
          <h2>Wprowadzenie</h2>
          <p>{escape(str(lesson['intro']))}</p>
        </section>

        <section>
          <h2>Objaśnienia</h2>
          <p>{escape(str(lesson['explanation']))}</p>
        </section>

        <section>
          <h2>Przykłady</h2>
          <ul>{examples_html}</ul>
        </section>

        <section>
          <h2>Ćwiczenie</h2>
          <p>{escape(str(lesson['exercise']))}</p>
        </section>

        <nav class='nav'>
          {prev_button}
          {next_button}
          <a class='btn' href='/kurs/sql'>Wróć do spisu</a>
        </nav>
        """,
        title=f"{lesson['title']} – Kurs SQL",
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
