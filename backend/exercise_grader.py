from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from backend.sql_runner import SqlExecutionResult, SqlRunner


@dataclass
class GradeResult:
    status: str
    feedback: str


class ExerciseGrader:
    CLAUSE_PATTERNS: dict[str, str] = {
        "WHERE": r"\bWHERE\b",
        "JOIN": r"\bJOIN\b",
        "GROUP BY": r"\bGROUP\s+BY\b",
        "HAVING": r"\bHAVING\b",
        "ORDER BY": r"\bORDER\s+BY\b",
        "LIMIT": r"\bLIMIT\b",
        "WITH": r"\bWITH\b",
        "DISTINCT": r"\bDISTINCT\b",
        "COALESCE": r"\bCOALESCE\s*\(",
        "WINDOW": r"\bOVER\s*\(",
        "SUBQUERY": r"\(\s*SELECT\b",
    }

    def __init__(self, lessons_dir: Path, runner: SqlRunner) -> None:
        self.lessons_dir = lessons_dir
        self.runner = runner
        self._lessons_by_key = self._load_lessons()

    def _load_lessons(self) -> dict[str, dict[str, Any]]:
        lessons: dict[str, dict[str, Any]] = {}
        for lesson_path in sorted(self.lessons_dir.glob("*.json")):
            lesson = json.loads(lesson_path.read_text(encoding="utf-8"))
            keys = {
                str(lesson.get("id", "")).strip(),
                str(lesson.get("slug", "")).strip(),
                lesson_path.stem,
            }
            for key in {key for key in keys if key}:
                lessons[key] = lesson
        return lessons

    def grade(self, lesson_id: str, sql: str, actual: SqlExecutionResult) -> GradeResult:
        lesson = self._lessons_by_key.get(lesson_id)
        if lesson is None:
            return GradeResult(
                status="fail",
                feedback="Nie znaleziono konfiguracji walidacji dla tej lekcji.",
            )

        validation = lesson.get("validation") or {}
        if actual.error:
            return GradeResult(status="fail", feedback=f"Zapytanie zwróciło błąd: {actual.error}")

        semantic_errors = self._validate_semantic_rules(sql=sql, validation=validation)
        if semantic_errors:
            return GradeResult(status="fail", feedback=" ".join(semantic_errors))

        expected_sql = validation.get("expectedSql")
        if not isinstance(expected_sql, str) or not expected_sql.strip():
            return GradeResult(status="fail", feedback="Brak zapytania wzorcowego dla lekcji.")

        expected = self.runner.execute(lesson_id=lesson_id, sql=expected_sql)
        if expected.error:
            return GradeResult(
                status="fail",
                feedback="Błąd konfiguracji lekcji: zapytanie wzorcowe nie wykonało się poprawnie.",
            )

        comparison = validation.get("comparison") or {}
        equal, mismatch_reason = self._compare_results(
            actual=actual,
            expected=expected,
            ignore_row_order=bool(comparison.get("ignoreRowOrder", False)),
            ignore_column_order=bool(comparison.get("ignoreColumnOrder", False)),
            numeric_tolerance=float(comparison.get("numericTolerance", 0.0)),
        )

        if equal:
            return GradeResult(status="pass", feedback="✅ Świetnie! Wynik zapytania jest poprawny.")

        return GradeResult(
            status="fail",
            feedback=f"❌ Wynik różni się od oczekiwanego: {mismatch_reason}",
        )

    def _validate_semantic_rules(self, sql: str, validation: dict[str, Any]) -> list[str]:
        semantic_rules = validation.get("semanticRules") or {}
        required_clauses = semantic_rules.get("requiredClauses") or []
        sql_upper = sql.upper()

        missing = []
        for clause in required_clauses:
            pattern = self.CLAUSE_PATTERNS.get(clause)
            if pattern and not re.search(pattern, sql_upper):
                missing.append(clause)

        if not missing:
            return []

        joined = ", ".join(missing)
        return [f"Brakuje wymaganych elementów składni: {joined}."]

    def _compare_results(
        self,
        actual: SqlExecutionResult,
        expected: SqlExecutionResult,
        ignore_row_order: bool,
        ignore_column_order: bool,
        numeric_tolerance: float,
    ) -> tuple[bool, str]:
        actual_columns = actual.columns
        expected_columns = expected.columns

        if ignore_column_order:
            if set(actual_columns) != set(expected_columns):
                return False, "zestaw kolumn jest inny niż oczekiwany"
            reorder_indices = [actual_columns.index(col) for col in expected_columns]
            actual_rows = [[row[index] for index in reorder_indices] for row in actual.rows]
            actual_columns = expected_columns
        else:
            if actual_columns != expected_columns:
                return False, f"kolejność lub nazwy kolumn są niepoprawne (otrzymano: {actual_columns})"
            actual_rows = actual.rows

        if len(actual_rows) != len(expected.rows):
            return False, f"liczba wierszy jest niepoprawna (otrzymano {len(actual_rows)}, oczekiwano {len(expected.rows)})"

        actual_norm = [
            [self._normalize_value(value, numeric_tolerance) for value in row] for row in actual_rows
        ]
        expected_norm = [
            [self._normalize_value(value, numeric_tolerance) for value in row] for row in expected.rows
        ]

        if ignore_row_order:
            actual_norm = sorted(actual_norm, key=repr)
            expected_norm = sorted(expected_norm, key=repr)

        if actual_norm != expected_norm:
            return False, "wartości w komórkach nie zgadzają się z oczekiwanym wynikiem"

        return True, "ok"

    def _normalize_value(self, value: Any, numeric_tolerance: float) -> Any:
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            if numeric_tolerance > 0:
                precision = max(0, math.ceil(-math.log10(numeric_tolerance)))
                return round(float(value), precision)
            return float(value)
        return value
