from pathlib import Path

import pytest

from backend.sql_runner import SqlRunner, SqlValidationError


@pytest.fixture
def runner(tmp_path: Path) -> SqlRunner:
    schema_path = tmp_path / "schema.sql"
    seed_path = tmp_path / "seed.sql"
    runtime_dir = tmp_path / "runtime"

    schema_path.write_text("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT);", encoding="utf-8")
    seed_path.write_text("INSERT INTO users (id, name) VALUES (1, 'Ala'), (2, 'Ola');", encoding="utf-8")

    return SqlRunner(
        schema_path=schema_path,
        seed_path=seed_path,
        runtime_dir=runtime_dir,
        max_rows=1,
        max_output_bytes=10_000,
    )


def test_execute_returns_rows_and_truncation_flag(runner: SqlRunner) -> None:
    result = runner.execute("lesson", "SELECT id FROM users ORDER BY id")

    assert result.error is None
    assert result.columns == ["id"]
    assert result.rows == [[1]]
    assert result.truncated is True


def test_validate_rejects_non_select(runner: SqlRunner) -> None:
    with pytest.raises(SqlValidationError, match="SELECT/WITH"):
        runner.execute("lesson", "DELETE FROM users")


def test_reset_base_snapshot_restores_seed_state(runner: SqlRunner) -> None:
    result = runner.execute("lesson", "SELECT COUNT(*) AS cnt FROM users")
    assert result.rows == [[2]]

    import sqlite3

    conn = sqlite3.connect(runner.base_db_path)
    try:
        conn.execute("DELETE FROM users")
        conn.commit()
    finally:
        conn.close()

    result_after_delete = runner.execute("lesson", "SELECT COUNT(*) AS cnt FROM users")
    assert result_after_delete.rows == [[0]]

    runner.reset_base_snapshot()

    result_after_reset = runner.execute("lesson", "SELECT COUNT(*) AS cnt FROM users")
    assert result_after_reset.rows == [[2]]
