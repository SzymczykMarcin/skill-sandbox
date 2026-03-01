from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
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
