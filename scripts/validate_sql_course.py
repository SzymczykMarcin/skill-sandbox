#!/usr/bin/env python3
import json
import sys
from pathlib import Path

REQUIRED_FIELDS = {
    "id",
    "slug",
    "title",
    "level",
    "order",
    "intro",
    "explanation",
    "examples",
    "exercise",
    "solutionHints",
    "expectedQueryPatterns",
    "validation",
}
ALLOWED_LEVELS = {"beginner", "intermediate", "advanced"}
REQUIRED_VALIDATION_FIELDS = {"expectedSql", "comparison", "semanticRules"}
REQUIRED_COMPARISON_FIELDS = {"ignoreRowOrder", "ignoreColumnOrder", "numericTolerance"}


def validate_content_dir(content_dir: Path) -> int:
    lesson_files = sorted(content_dir.glob("*.json"))
    if not lesson_files:
        print(f"ERROR: Brak plików JSON w {content_dir}")
        return 1

    seen_slugs = {}
    seen_ids = {}
    orders = []
    errors = []

    for file_path in lesson_files:
        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"{file_path}: niepoprawny JSON ({exc})")
            continue

        if not isinstance(data, dict):
            errors.append(f"{file_path}: lekcja musi być obiektem JSON")
            continue

        missing = sorted(REQUIRED_FIELDS - set(data.keys()))
        if missing:
            errors.append(f"{file_path}: brak wymaganych pól: {', '.join(missing)}")
            continue

        lesson_id = data.get("id")
        slug = data.get("slug")
        order = data.get("order")
        level = data.get("level")

        if not isinstance(lesson_id, str) or not lesson_id.strip():
            errors.append(f"{file_path}: pole 'id' musi być niepustym stringiem")
        elif lesson_id in seen_ids:
            errors.append(
                f"{file_path}: duplikat id '{lesson_id}' (pierwszy raz w {seen_ids[lesson_id]})"
            )
        else:
            seen_ids[lesson_id] = file_path.name

        if not isinstance(slug, str) or not slug.strip():
            errors.append(f"{file_path}: pole 'slug' musi być niepustym stringiem")
        elif slug in seen_slugs:
            errors.append(
                f"{file_path}: duplikat slug '{slug}' (pierwszy raz w {seen_slugs[slug]})"
            )
        else:
            seen_slugs[slug] = file_path.name

        if isinstance(order, int):
            orders.append(order)
        else:
            errors.append(f"{file_path}: pole 'order' musi być liczbą całkowitą")

        if level not in ALLOWED_LEVELS:
            errors.append(
                f"{file_path}: pole 'level' musi należeć do {sorted(ALLOWED_LEVELS)}"
            )

        if not isinstance(data.get("examples"), list) or len(data["examples"]) == 0:
            errors.append(f"{file_path}: pole 'examples' musi być niepustą listą")

        if not isinstance(data.get("solutionHints"), list) or len(data["solutionHints"]) == 0:
            errors.append(f"{file_path}: pole 'solutionHints' musi być niepustą listą")

        if (
            not isinstance(data.get("expectedQueryPatterns"), list)
            or len(data["expectedQueryPatterns"]) == 0
        ):
            errors.append(
                f"{file_path}: pole 'expectedQueryPatterns' musi być niepustą listą"
            )

        validation = data.get("validation")
        if not isinstance(validation, dict):
            errors.append(f"{file_path}: pole 'validation' musi być obiektem")
            continue

        missing_validation = sorted(REQUIRED_VALIDATION_FIELDS - set(validation.keys()))
        if missing_validation:
            errors.append(
                f"{file_path}: brak pól validation: {', '.join(missing_validation)}"
            )
            continue

        if not isinstance(validation.get("expectedSql"), str) or not validation["expectedSql"].strip():
            errors.append(f"{file_path}: validation.expectedSql musi być niepustym stringiem")

        comparison = validation.get("comparison")
        if not isinstance(comparison, dict):
            errors.append(f"{file_path}: validation.comparison musi być obiektem")
        else:
            missing_comparison = sorted(REQUIRED_COMPARISON_FIELDS - set(comparison.keys()))
            if missing_comparison:
                errors.append(
                    f"{file_path}: brak pól validation.comparison: {', '.join(missing_comparison)}"
                )
            if not isinstance(comparison.get("ignoreRowOrder"), bool):
                errors.append(f"{file_path}: validation.comparison.ignoreRowOrder musi być bool")
            if not isinstance(comparison.get("ignoreColumnOrder"), bool):
                errors.append(f"{file_path}: validation.comparison.ignoreColumnOrder musi być bool")
            if not isinstance(comparison.get("numericTolerance"), (int, float)):
                errors.append(f"{file_path}: validation.comparison.numericTolerance musi być liczbą")

        semantic_rules = validation.get("semanticRules")
        if not isinstance(semantic_rules, dict):
            errors.append(f"{file_path}: validation.semanticRules musi być obiektem")
        elif not isinstance(semantic_rules.get("requiredClauses", []), list):
            errors.append(f"{file_path}: validation.semanticRules.requiredClauses musi być listą")

    if orders:
        min_order = min(orders)
        max_order = max(orders)
        expected = set(range(min_order, max_order + 1))
        missing_orders = sorted(expected - set(orders))
        if missing_orders:
            errors.append(
                "Brakujące wartości 'order' w sekwencji: "
                + ", ".join(str(x) for x in missing_orders)
            )

        duplicate_orders = sorted({x for x in orders if orders.count(x) > 1})
        if duplicate_orders:
            errors.append(
                "Powielone wartości 'order': "
                + ", ".join(str(x) for x in duplicate_orders)
            )

    if errors:
        print("Walidacja nieudana:")
        for err in errors:
            print(f" - {err}")
        return 1

    print(f"OK: zwalidowano {len(lesson_files)} lekcji w {content_dir}")
    return 0


if __name__ == "__main__":
    base_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("content/sql-course")
    sys.exit(validate_content_dir(base_dir))
