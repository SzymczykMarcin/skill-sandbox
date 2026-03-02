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
            "<article class='lesson-card'>"
            "<div class='lesson-card-header'>"
            f"<span class='lesson-number'>Lekcja #{lesson['order']}</span>"
            f"<span class='lesson-status not-started' data-lesson-status='{escape(str(lesson['slug']))}'>Nie rozpoczęta</span>"
            "</div>"
            f"<h2><a href='/kurs/sql/{escape(str(lesson['slug']))}'>{escape(str(lesson['title']))}</a></h2>"
            f"<p class='lesson-description muted'>{escape(str(lesson.get('intro') or lesson.get('exercise') or 'Poznaj najważniejsze zagadnienia tej lekcji.'))}</p>"
            f"<a class='btn btn-primary' href='/kurs/sql/{escape(str(lesson['slug']))}'>Otwórz lekcję</a>"
            "</article>"
        )
        for lesson in lessons
    )

    content = f"""
        <section class='hero'>
          <h1>Kurs SQL – spis lekcji</h1>
          <p class='muted'>
            Przejdź przez kolejne lekcje i ćwicz SQL na żywych przykładach,
            żeby szybko budować poprawne zapytania.
          </p>
          <a id='continue-learning' class='btn btn-primary disabled' href='/kurs/sql'>Kontynuuj naukę</a>
        </section>

        <div class='toolbar'>
          <button id='reset-progress' class='btn btn-secondary' type='button'>Resetuj postęp</button>
        </div>
        <section class='lessons-grid'>{lesson_items}</section>
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
        f"<a class='btn btn-secondary' href='/kurs/sql/{escape(str(prev_lesson['slug']))}'>Poprzednie ćwiczenie</a>"
        if prev_lesson
        else "<span class='btn btn-secondary disabled'>Poprzednie ćwiczenie</span>"
    )
    next_button = (
        f"<a class='btn btn-primary' href='/kurs/sql/{escape(str(next_lesson['slug']))}'>Następne ćwiczenie</a>"
        if next_lesson
        else "<span class='btn btn-primary disabled'>Następne ćwiczenie</span>"
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
        <a class='skip-link' href='#lesson-main-content'>Przejdź do treści lekcji</a>

        <header>
          <h1>{escape(str(lesson['title']))}</h1>
          <p class='muted'>Lekcja #{lesson['order']}</p>
        </header>

        <div class='lesson-layout'>
          <main id='lesson-main-content' class='lesson-main'>
            <section class='surface-card'>
              <h2>Wprowadzenie</h2>
              <p>{escape(str(lesson['intro']))}</p>
            </section>

            <section class='surface-card'>
              <h2>Objaśnienia</h2>
              <p>{escape(str(lesson['explanation']))}</p>
            </section>

            <section class='surface-card'>
              <h2>Przykłady</h2>
              <ul>{examples_html}</ul>
            </section>

            <section class='surface-card callout callout-exercise'>
              <h2>Ćwiczenie</h2>
              <p>{escape(str(lesson['exercise']))}</p>
            </section>
          </main>

          <aside class='lesson-sidebar'>
            <section class='surface-card'>
              <h2>SQL Playground</h2>
              <div class='editor-shell'>
                <div id='sql-editor' class='editor-container'></div>
              </div>
              <div class='actions'>
                <button id='run-query' class='btn btn-primary' type='button'>
                  <span class='btn-spinner' aria-hidden='true'></span>
                  <span class='btn-label'>Uruchom zapytanie</span>
                </button>
                <button id='reset-query' class='btn btn-secondary' type='button'>Resetuj zapytanie</button>
                <button id='show-hint' class='btn btn-ghost' type='button'>Pokaż podpowiedź</button>
                <span class='muted'>Skrót: Ctrl/Cmd + Enter</span>
              </div>
              <div id='hint-box' class='callout callout-hint' aria-live='polite' aria-atomic='true' hidden></div>
              <div id='toast-region' class='toast-region' aria-live='polite' aria-atomic='true'></div>
              <div id='query-status' class='status muted' role='status' aria-live='polite' aria-atomic='true'>Gotowe do uruchomienia zapytania.</div>
              <div id='result-meta' class='meta'></div>
              <div id='result-area'></div>
            </section>

            <nav class='nav' aria-label='Nawigacja pomiędzy lekcjami'>
              {prev_button}
              {next_button}
              <a class='btn btn-ghost' href='/kurs/sql'>Wróć do spisu</a>
            </nav>
          </aside>
        </div>

        <script>window.LESSON_CONTEXT = {lesson_json};</script>
        <script src='/static/js/progress.js'></script>
        <script src='/static/js/lesson-page.js'></script>
    """
    return render_layout(content=content, title=f"{lesson['title']} – Kurs SQL")
