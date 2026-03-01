from __future__ import annotations

import re
import sqlite3
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


BLOCKED_KEYWORDS = {
    "ATTACH",
    "DETACH",
    "PRAGMA",
    "DROP",
    "ALTER",
    "VACUUM",
    "REINDEX",
    "ANALYZE",
    "CREATE",
}


@dataclass
class SqlExecutionResult:
    columns: list[str]
    rows: list[list[Any]]
    execution_ms: float
    error: str | None
    truncated: bool


class SqlValidationError(ValueError):
    """Raised when SQL does not meet course safety constraints."""


class SqlRunner:
    def __init__(
        self,
        schema_path: Path,
        seed_path: Path,
        runtime_dir: Path,
        base_db_path: Path | None = None,
        query_timeout_s: float = 3.0,
        max_rows: int = 200,
    ) -> None:
        self.schema_path = schema_path
        self.seed_path = seed_path
        self.runtime_dir = runtime_dir
        self.base_db_path = base_db_path or runtime_dir / "base_snapshot.sqlite"
        self.query_timeout_s = query_timeout_s
        self.max_rows = max_rows
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self._ensure_base_snapshot()

    def _ensure_base_snapshot(self) -> None:
        if self.base_db_path.exists():
            return

        conn = sqlite3.connect(self.base_db_path)
        try:
            conn.executescript(self.schema_path.read_text(encoding="utf-8"))
            conn.executescript(self.seed_path.read_text(encoding="utf-8"))
            conn.commit()
        finally:
            conn.close()

    def _make_working_connection(self) -> tuple[sqlite3.Connection, Path]:
        temp = tempfile.NamedTemporaryFile(prefix="sql-runner-", suffix=".sqlite", delete=False)
        temp_path = Path(temp.name)
        temp.close()

        source = sqlite3.connect(self.base_db_path)
        target = sqlite3.connect(temp_path)
        try:
            source.backup(target)
            target.commit()
        finally:
            source.close()

        return target, temp_path

    def _normalize_sql(self, sql: str) -> str:
        no_line_comments = re.sub(r"--.*?$", "", sql, flags=re.MULTILINE)
        no_block_comments = re.sub(r"/\*.*?\*/", "", no_line_comments, flags=re.DOTALL)
        return no_block_comments.strip()

    def _validate_sql(self, sql: str) -> str:
        normalized = self._normalize_sql(sql)
        if not normalized:
            raise SqlValidationError("SQL nie może być pusty.")

        statements = [part.strip() for part in normalized.split(";") if part.strip()]
        if len(statements) != 1:
            raise SqlValidationError("Dozwolone jest tylko pojedyncze zapytanie SQL.")

        statement = statements[0]
        first_token_match = re.match(r"^([a-zA-Z_]+)", statement)
        first_token = first_token_match.group(1).upper() if first_token_match else ""
        if first_token not in {"SELECT", "WITH"}:
            raise SqlValidationError("W kursie dozwolone są wyłącznie zapytania SELECT/WITH.")

        upper_statement = statement.upper()
        for keyword in BLOCKED_KEYWORDS:
            if re.search(rf"\b{keyword}\b", upper_statement):
                raise SqlValidationError(f"Wykryto zablokowaną komendę: {keyword}.")

        return statement

    def execute(self, lesson_id: str, sql: str) -> SqlExecutionResult:
        # lesson_id is part of API contract and can be used for lesson-specific rules later.
        _ = lesson_id
        statement = self._validate_sql(sql)
        conn, temp_path = self._make_working_connection()
        started = time.monotonic()

        try:
            deadline = started + self.query_timeout_s

            def progress_handler() -> int:
                if time.monotonic() > deadline:
                    return 1
                return 0

            conn.set_progress_handler(progress_handler, 1_000)
            cursor = conn.execute(statement)
            fetched = cursor.fetchmany(self.max_rows + 1)
            columns = [description[0] for description in (cursor.description or [])]
            truncated = len(fetched) > self.max_rows
            rows = fetched[: self.max_rows]
            execution_ms = (time.monotonic() - started) * 1000

            return SqlExecutionResult(
                columns=columns,
                rows=[list(row) for row in rows],
                execution_ms=execution_ms,
                error=None,
                truncated=truncated,
            )
        except sqlite3.OperationalError as exc:
            execution_ms = (time.monotonic() - started) * 1000
            error_message = "Przekroczono limit czasu wykonania zapytania."
            if "interrupted" not in str(exc).lower():
                error_message = str(exc)
            return SqlExecutionResult(
                columns=[],
                rows=[],
                execution_ms=execution_ms,
                error=error_message,
                truncated=False,
            )
        finally:
            conn.close()
            temp_path.unlink(missing_ok=True)
