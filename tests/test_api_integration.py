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
