from __future__ import annotations

import json
from html import escape


def render_layout(content: str, title: str) -> str:
    return f"""
<!doctype html>
<html lang="pl">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{escape(title)}</title>
    <link rel="stylesheet" href="/static/css/sql-course.css" />
  </head>
  <body>
    {content}
  </body>
</html>
""".strip()


def render_course_index(lessons: list[dict[str, object]]) -> str:
    lesson_items = "\n".join(
        (
            f"<li><a href='/kurs/sql/{escape(str(lesson['slug']))}'>{escape(str(lesson['title']))}</a> "
            f"<span class='muted'>(#{lesson['order']})</span>"
            f"<span class='lesson-status' data-lesson-status='{escape(str(lesson['slug']))}'>Nie rozpoczęta</span></li>"
        )
        for lesson in lessons
    )

    content = f"""
        <h1>Kurs SQL – spis lekcji</h1>
        <div class='toolbar'>
          <a id='continue-learning' class='btn disabled' href='/kurs/sql'>Kontynuuj naukę</a>
          <button id='reset-progress' class='btn' type='button'>Resetuj postęp</button>
        </div>
        <ul>{lesson_items}</ul>
        <script src='/static/js/progress.js'></script>
        <script src='/static/js/course-index.js'></script>
    """
    return render_layout(content=content, title="Kurs SQL – spis lekcji")


def render_lesson_page(
    lesson: dict[str, object],
    prev_lesson: dict[str, object] | None,
    next_lesson: dict[str, object] | None,
) -> str:
    examples_html = "".join(
        f"<li><p>{escape(str(example['description']))}</p><pre>{escape(str(example['query']))}</pre></li>"
        for example in lesson["examples"]
    )

    prev_button = (
        f"<a class='btn' href='/kurs/sql/{escape(str(prev_lesson['slug']))}'>Poprzednie ćwiczenie</a>"
        if prev_lesson
        else "<span class='btn disabled'>Poprzednie ćwiczenie</span>"
    )
    next_button = (
        f"<a class='btn' href='/kurs/sql/{escape(str(next_lesson['slug']))}'>Następne ćwiczenie</a>"
        if next_lesson
        else "<span class='btn disabled'>Następne ćwiczenie</span>"
    )

    lesson_json = json.dumps(
        {
            "slug": lesson["slug"],
            "starterQuery": lesson.get("starterQuery")
            or lesson.get("validation", {}).get("expectedSql")
            or "SELECT * FROM users LIMIT 10;",
            "solutionHints": lesson.get("solutionHints") or [],
        },
        ensure_ascii=False,
    )

    content = f"""
        <h1>{escape(str(lesson['title']))}</h1>
        <p class='muted'>Lekcja #{lesson['order']}</p>

        <section>
          <h2>Wprowadzenie</h2>
          <p>{escape(str(lesson['intro']))}</p>
        </section>

        <section>
          <h2>Objaśnienia</h2>
          <p>{escape(str(lesson['explanation']))}</p>
        </section>

        <section>
          <h2>Przykłady</h2>
          <ul>{examples_html}</ul>
        </section>

        <section>
          <h2>Ćwiczenie</h2>
          <p>{escape(str(lesson['exercise']))}</p>
        </section>

        <section>
          <h2>SQL Playground</h2>
          <div class='editor-shell'>
            <div id='sql-editor' class='editor-container'></div>
          </div>
          <div class='actions'>
            <button id='run-query' class='btn' type='button'>Uruchom zapytanie</button>
            <button id='reset-query' class='btn' type='button'>Resetuj zapytanie</button>
            <button id='show-hint' class='btn' type='button'>Pokaż podpowiedź</button>
            <span class='muted'>Skrót: Ctrl/Cmd + Enter</span>
          </div>
          <div id='hint-box' class='status muted' hidden></div>
          <div id='query-status' class='status muted'>Gotowe do uruchomienia zapytania.</div>
          <div id='result-meta' class='meta'></div>
          <div id='result-area'></div>
        </section>

        <nav class='nav'>
          {prev_button}
          {next_button}
          <a class='btn' href='/kurs/sql'>Wróć do spisu</a>
        </nav>

        <script>window.LESSON_CONTEXT = {lesson_json};</script>
        <script src='/static/js/progress.js'></script>
        <script src='/static/js/lesson-page.js'></script>
    """
    return render_layout(content=content, title=f"{lesson['title']} – Kurs SQL")
