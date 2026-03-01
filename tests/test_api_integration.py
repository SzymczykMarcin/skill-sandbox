import sqlite3

from fastapi.testclient import TestClient

from backend import main


client = TestClient(main.app)


def test_get_lesson_page_returns_html() -> None:
    response = client.get("/kurs/sql/01-select-basics")

    assert response.status_code == 200
    assert "SQL Playground" in response.text


def test_execute_query_returns_data() -> None:
    response = client.post(
        "/execute",
        json={"lessonId": "01-select-basics", "sql": "SELECT COUNT(*) AS cnt FROM users"},
    )

    payload = response.json()
    assert response.status_code == 200
    assert payload["error"] is None
    assert payload["columns"] == ["cnt"]
    assert payload["rows"][0][0] > 0


def test_get_lessons_returns_lesson_summaries() -> None:
    response = client.get("/lessons")

    payload = response.json()
    assert response.status_code == 200
    assert isinstance(payload, list)
    assert len(payload) > 0
    assert all({"slug", "title", "level", "order"}.issubset(lesson.keys()) for lesson in payload)
    assert "description" in payload[0]


def test_get_lesson_returns_full_lesson_by_slug() -> None:
    slug = main.load_lessons()[0]["slug"]

    response = client.get(f"/lessons/{slug}")

    payload = response.json()
    assert response.status_code == 200
    assert payload["slug"] == slug
    assert payload["intro"]
    assert payload["exercise"]
    assert payload["validation"]


def test_get_lesson_returns_404_for_unknown_slug() -> None:
    response = client.get("/lessons/does-not-exist")

    assert response.status_code == 404
    assert response.json()["detail"] == "Nie znaleziono lekcji o podanym slug"


def test_reset_db_rebuilds_base_snapshot() -> None:
    conn = sqlite3.connect(main.runner.base_db_path)
    try:
        conn.execute("DELETE FROM users")
        conn.commit()
    finally:
        conn.close()

    modified = client.post(
        "/execute",
        json={"lessonId": "01-select-basics", "sql": "SELECT COUNT(*) AS cnt FROM users"},
    )
    assert modified.json()["rows"] == [[0]]

    reset_response = client.post("/reset-db")
    assert reset_response.status_code == 200
    assert reset_response.json()["status"] == "ok"

    restored = client.post(
        "/execute",
        json={"lessonId": "01-select-basics", "sql": "SELECT COUNT(*) AS cnt FROM users"},
    )
    assert restored.json()["rows"][0][0] > 0
