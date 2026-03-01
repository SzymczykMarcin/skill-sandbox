from pathlib import Path

from scripts.validate_sql_course import validate_content_dir


def _write_lesson(path: Path, *, lesson_id: str = "01", slug: str = "lesson-01", order: int = 1) -> None:
    path.write_text(
        """
{
  "id": "%s",
  "slug": "%s",
  "title": "Tytuł",
  "level": "beginner",
  "order": %d,
  "intro": "Wstęp",
  "explanation": "Opis",
  "examples": [{"description": "Przykład", "query": "SELECT 1"}],
  "exercise": "Zadanie",
  "solutionHints": ["Hint"],
  "expectedQueryPatterns": ["SELECT"],
  "validation": {
    "expectedSql": "SELECT 1",
    "comparison": {
      "ignoreRowOrder": false,
      "ignoreColumnOrder": false,
      "numericTolerance": 0
    },
    "semanticRules": {
      "requiredClauses": []
    }
  }
}
""".strip()
        % (lesson_id, slug, order),
        encoding="utf-8",
    )


def test_validator_accepts_valid_content(tmp_path, capsys) -> None:
    _write_lesson(tmp_path / "01.json")

    result = validate_content_dir(tmp_path)
    output = capsys.readouterr().out

    assert result == 0
    assert "OK: zwalidowano 1 lekcji" in output


def test_validator_rejects_duplicate_slug(tmp_path, capsys) -> None:
    _write_lesson(tmp_path / "01.json", lesson_id="01", slug="dupe", order=1)
    _write_lesson(tmp_path / "02.json", lesson_id="02", slug="dupe", order=2)

    result = validate_content_dir(tmp_path)
    output = capsys.readouterr().out

    assert result == 1
    assert "duplikat slug 'dupe'" in output


def test_validator_rejects_missing_order_sequence(tmp_path, capsys) -> None:
    _write_lesson(tmp_path / "01.json", lesson_id="01", slug="one", order=1)
    _write_lesson(tmp_path / "03.json", lesson_id="03", slug="three", order=3)

    result = validate_content_dir(tmp_path)
    output = capsys.readouterr().out

    assert result == 1
    assert "Brakujące wartości 'order'" in output
