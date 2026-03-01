import re

from fastapi.testclient import TestClient

from backend import main


client = TestClient(main.app)


def _extract_link(response_text: str, label: str) -> str:
    pattern = rf"<a class='btn' href='([^']+)'>{label}</a>"
    match = re.search(pattern, response_text)
    assert match is not None
    return match.group(1)


def test_e2e_lesson_navigation_and_execution_flow() -> None:
    lesson_response = client.get("/kurs/sql/01-select-basics")
    assert lesson_response.status_code == 200

    execute_response = client.post(
        "/execute",
        json={"lessonId": "01-select-basics", "sql": "SELECT id FROM users ORDER BY id LIMIT 1"},
    )
    execute_payload = execute_response.json()

    assert execute_response.status_code == 200
    assert execute_payload["error"] is None
    assert execute_payload["gradingStatus"] in {"pass", "fail"}

    next_href = _extract_link(lesson_response.text, "Następne ćwiczenie")
    next_response = client.get(next_href)
    assert next_response.status_code == 200

    prev_href = _extract_link(next_response.text, "Poprzednie ćwiczenie")
    prev_response = client.get(prev_href)
    assert prev_response.status_code == 200
    assert "Lekcja #1" in prev_response.text
