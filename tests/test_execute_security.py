from fastapi.testclient import TestClient

from backend import main


client = TestClient(main.app)


def test_rejects_invalid_lesson_id_format() -> None:
    response = client.post("/execute", json={"lessonId": "../etc/passwd", "sql": "SELECT 1"})

    assert response.status_code == 422


def test_rejects_too_long_sql_payload() -> None:
    long_sql = "SELECT 1 " + "x" * 6000
    response = client.post("/execute", json={"lessonId": "01-select-basics", "sql": long_sql})

    assert response.status_code == 422


def test_rate_limiting_on_execute(monkeypatch) -> None:
    limiter = main.InMemoryRateLimiter(max_requests=1, window_s=60)
    monkeypatch.setattr(main, "rate_limiter", limiter)

    first = client.post("/execute", json={"lessonId": "01-select-basics", "sql": "SELECT 1"})
    second = client.post("/execute", json={"lessonId": "01-select-basics", "sql": "SELECT 1"})

    assert first.status_code == 200
    assert second.status_code == 429


def test_query_timeout_returns_safe_message(monkeypatch) -> None:
    monkeypatch.setattr(main.runner, "query_timeout_s", 0.0001)

    response = client.post(
        "/execute",
        json={
            "lessonId": "01-select-basics",
            "sql": "WITH RECURSIVE cnt(x) AS (SELECT 1 UNION ALL SELECT x+1 FROM cnt) SELECT x FROM cnt",
        },
    )

    payload = response.json()
    assert response.status_code == 200
    assert payload["error"] == "Przekroczono limit czasu wykonania zapytania."


def test_response_memory_limit_blocks_oversized_output(monkeypatch) -> None:
    monkeypatch.setattr(main.runner, "max_output_bytes", 40)

    response = client.post(
        "/execute",
        json={"lessonId": "01-select-basics", "sql": "SELECT printf('%050d', 1) AS padded"},
    )

    payload = response.json()
    assert response.status_code == 200
    assert payload["error"] == "Wynik zapytania przekracza dopuszczalny limit pamięci odpowiedzi."
