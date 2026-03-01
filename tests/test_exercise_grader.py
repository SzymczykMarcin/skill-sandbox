import json
from pathlib import Path

from backend.exercise_grader import ExerciseGrader
from backend.sql_runner import SqlExecutionResult


class StubRunner:
    def execute(self, lesson_id: str, sql: str) -> SqlExecutionResult:
        _ = lesson_id
        if sql == "SELECT 1 AS value":
            return SqlExecutionResult(columns=["value"], rows=[[1.0]], execution_ms=1.0, error=None, truncated=False)
        return SqlExecutionResult(columns=[], rows=[], execution_ms=1.0, error="boom", truncated=False)


def _lesson_payload() -> dict:
    return {
        "id": "lesson-1",
        "slug": "lesson-1",
        "title": "Lekcja",
        "level": "beginner",
        "order": 1,
        "intro": "",
        "explanation": "",
        "examples": [{"description": "d", "query": "SELECT 1"}],
        "exercise": "",
        "solutionHints": ["h"],
        "expectedQueryPatterns": ["SELECT"],
        "validation": {
            "expectedSql": "SELECT 1 AS value",
            "comparison": {
                "ignoreRowOrder": False,
                "ignoreColumnOrder": False,
                "numericTolerance": 0.01,
            },
            "semanticRules": {"requiredClauses": ["WHERE"]},
        },
    }


def _write_lesson(tmp_path: Path) -> None:
    (tmp_path / "lesson-1.json").write_text(json.dumps(_lesson_payload()), encoding="utf-8")


def test_grade_fails_when_required_clause_missing(tmp_path: Path) -> None:
    _write_lesson(tmp_path)
    grader = ExerciseGrader(lessons_dir=tmp_path, runner=StubRunner())

    actual = SqlExecutionResult(columns=["value"], rows=[[1]], execution_ms=1.0, error=None, truncated=False)
    result = grader.grade(lesson_id="lesson-1", sql="SELECT 1", actual=actual)

    assert result.status == "fail"
    assert "Brakuje wymaganych elementów składni: WHERE" in result.feedback


def test_grade_passes_with_numeric_tolerance(tmp_path: Path) -> None:
    _write_lesson(tmp_path)
    grader = ExerciseGrader(lessons_dir=tmp_path, runner=StubRunner())

    actual = SqlExecutionResult(columns=["value"], rows=[[1.004]], execution_ms=1.0, error=None, truncated=False)
    result = grader.grade(lesson_id="lesson-1", sql="SELECT 1 WHERE 1=1", actual=actual)

    assert result.status == "pass"
    assert "Świetnie" in result.feedback
