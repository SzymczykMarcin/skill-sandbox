from __future__ import annotations

import json
import os
from functools import lru_cache
from html import escape
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from backend.exercise_grader import ExerciseGrader
from backend.sql_runner import SqlRunner, SqlValidationError


class ExecuteRequest(BaseModel):
    lessonId: str = Field(min_length=1)
    sql: str = Field(min_length=1)


class ExecuteResponse(BaseModel):
    columns: list[str]
    rows: list[list[object]]
    executionMs: float
    error: str | None
    truncated: bool
    gradingStatus: str
    feedback: str


repo_root = Path(__file__).resolve().parents[1]
runtime_dir = Path(os.getenv("SQLITE_RUNTIME_DIR", repo_root / ".runtime/sqlite"))
base_db_path_raw = os.getenv("SQLITE_BASE_DB_PATH")
base_db_path = Path(base_db_path_raw) if base_db_path_raw else None

runner = SqlRunner(
    schema_path=repo_root / "db/schema.sql",
    seed_path=repo_root / "db/seed.sql",
    runtime_dir=runtime_dir,
    base_db_path=base_db_path,
    query_timeout_s=float(os.getenv("SQL_QUERY_TIMEOUT_S", "3")),
    max_rows=int(os.getenv("SQL_MAX_ROWS", "200")),
)
grader = ExerciseGrader(lessons_dir=repo_root / "content/sql-course", runner=runner)

app = FastAPI()


@lru_cache(maxsize=1)
def load_lessons() -> list[dict[str, object]]:
    lessons_dir = repo_root / "content/sql-course"
    lessons: list[dict[str, object]] = []

    for lesson_file in lessons_dir.glob("*.json"):
        lesson = json.loads(lesson_file.read_text(encoding="utf-8"))
        lessons.append(lesson)

    lessons.sort(key=lambda lesson: int(lesson["order"]))
    return lessons


def render_layout(content: str, title: str) -> str:
    return f"""
<!doctype html>
<html lang="pl">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{escape(title)}</title>
    <style>
      body {{ font-family: Arial, sans-serif; margin: 2rem auto; max-width: 860px; line-height: 1.5; padding: 0 1rem; }}
      h1, h2 {{ margin-bottom: 0.5rem; }}
      ul {{ padding-left: 1.2rem; }}
      .nav {{ display: flex; gap: 0.75rem; flex-wrap: wrap; margin-top: 2rem; }}
      .btn {{ border: 1px solid #ccc; border-radius: 6px; padding: 0.5rem 0.75rem; text-decoration: none; color: #222; }}
      .btn.disabled {{ color: #999; border-color: #e2e2e2; pointer-events: none; }}
      pre {{ background: #f4f4f4; padding: 0.75rem; border-radius: 6px; overflow-x: auto; }}
      .muted {{ color: #666; }}
      .editor-shell {{ border: 1px solid #d7d7d7; border-radius: 8px; overflow: hidden; }}
      .editor-container {{ min-height: 220px; }}
      .editor-fallback {{ width: 100%; min-height: 220px; border: 0; padding: 0.75rem; box-sizing: border-box; font-family: Menlo, Consolas, monospace; }}
      .actions {{ display: flex; gap: 0.75rem; flex-wrap: wrap; margin-top: 0.75rem; align-items: center; }}
      button.btn {{ background: white; cursor: pointer; }}
      button.btn:disabled {{ color: #999; border-color: #e2e2e2; cursor: not-allowed; }}
      .status {{ margin-top: 0.75rem; font-size: 0.95rem; }}
      .status.loading {{ color: #1f4bb2; }}
      .status.error {{ color: #b00020; }}
      .status.success {{ color: #08620f; }}
      table {{ width: 100%; border-collapse: collapse; margin-top: 1rem; font-size: 0.95rem; }}
      th, td {{ border: 1px solid #ddd; padding: 0.4rem 0.55rem; text-align: left; vertical-align: top; }}
      th {{ background: #f8f8f8; }}
      .meta {{ margin-top: 0.5rem; color: #555; font-size: 0.92rem; }}
    </style>
  </head>
  <body>
    {content}
  </body>
</html>
""".strip()


@app.get("/kurs/sql", response_class=HTMLResponse)
@app.get("/kurs/sql/", response_class=HTMLResponse)
def sql_course_index() -> HTMLResponse:
    lesson_items = "\n".join(
        (
            f"<li><a href='/kurs/sql/{escape(str(lesson['slug']))}'>{escape(str(lesson['title']))}</a> "
            f"<span class='muted'>(#{lesson['order']})</span></li>"
        )
        for lesson in load_lessons()
    )

    html = render_layout(
        f"""
        <h1>Kurs SQL – spis lekcji</h1>
        <ul>{lesson_items}</ul>
        """,
        title="Kurs SQL – spis lekcji",
    )
    return HTMLResponse(content=html)


@app.get("/kurs/sql/{slug}", response_class=HTMLResponse)
def sql_course_lesson(slug: str) -> HTMLResponse:
    lessons = load_lessons()
    index_by_slug = {str(lesson["slug"]): idx for idx, lesson in enumerate(lessons)}

    if not slug:
        raise HTTPException(status_code=404, detail="Brak slug lekcji")
    if slug not in index_by_slug:
        raise HTTPException(status_code=404, detail="Nie znaleziono lekcji o podanym slug")

    lesson_index = index_by_slug[slug]
    lesson = lessons[lesson_index]

    prev_lesson = lessons[lesson_index - 1] if lesson_index > 0 else None
    next_lesson = lessons[lesson_index + 1] if lesson_index < len(lessons) - 1 else None

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

    html = render_layout(
        f"""
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

        <script>
          const LESSON_CONTEXT = {lesson_json};

          class SqlEditor {{
            constructor(container, initialValue) {{
              this.container = container;
              this.initialValue = initialValue;
              this.fallback = null;
              this.view = null;
            }}

            async mount() {{
              try {{
                await this._mountCodeMirror();
              }} catch (_error) {{
                this._mountFallback();
              }}
            }}

            async _mountCodeMirror() {{
              const [cmView, cmState, cmCommands, cmSql] = await Promise.all([
                import('https://esm.sh/@codemirror/view@6.36.2'),
                import('https://esm.sh/@codemirror/state@6.5.0'),
                import('https://esm.sh/@codemirror/commands@6.8.1'),
                import('https://esm.sh/@codemirror/lang-sql@6.10.0')
              ]);

              const customTheme = cmView.EditorView.theme({{
                '&': {{ minHeight: '220px', fontFamily: 'Menlo, Consolas, monospace', fontSize: '14px' }},
                '.cm-content': {{ minHeight: '220px' }}
              }});

              const onRunShortcut = cmView.keymap.of([
                {{ key: 'Mod-Enter', run: () => {{ window.runQuery(); return true; }} }},
                ...cmCommands.defaultKeymap
              ]);

              const state = cmState.EditorState.create({{
                doc: this.initialValue,
                extensions: [
                  cmView.keymap.of(cmCommands.defaultKeymap),
                  onRunShortcut,
                  cmSql.sql({{ upperCaseKeywords: true }}),
                  cmView.EditorView.lineWrapping,
                  customTheme
                ]
              }});

              this.view = new cmView.EditorView({{ state, parent: this.container }});
            }}

            _mountFallback() {{
              const textarea = document.createElement('textarea');
              textarea.className = 'editor-fallback';
              textarea.value = this.initialValue;
              textarea.addEventListener('keydown', (event) => {{
                if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {{
                  event.preventDefault();
                  window.runQuery();
                }}
              }});
              this.container.innerHTML = '';
              this.container.append(textarea);
              this.fallback = textarea;
            }}

            getValue() {{
              if (this.view) {{
                return this.view.state.doc.toString();
              }}
              return this.fallback ? this.fallback.value : '';
            }}

            setValue(value) {{
              if (this.view) {{
                const transaction = this.view.state.update({{
                  changes: {{ from: 0, to: this.view.state.doc.length, insert: value }}
                }});
                this.view.dispatch(transaction);
                this.view.focus();
                return;
              }}
              if (this.fallback) {{
                this.fallback.value = value;
                this.fallback.focus();
              }}
            }}
          }}

          const statusEl = document.getElementById('query-status');
          const metaEl = document.getElementById('result-meta');
          const resultArea = document.getElementById('result-area');
          const runBtn = document.getElementById('run-query');
          const resetBtn = document.getElementById('reset-query');
          const hintBtn = document.getElementById('show-hint');
          const hintBox = document.getElementById('hint-box');

          const editor = new SqlEditor(document.getElementById('sql-editor'), LESSON_CONTEXT.starterQuery);
          editor.mount();

          function setLoading(loading) {{
            runBtn.disabled = loading;
            resetBtn.disabled = loading;
            if (loading) {{
              statusEl.className = 'status loading';
              statusEl.textContent = 'Wykonywanie zapytania...';
            }}
          }}

          function renderTable(columns, rows) {{
            if (!columns.length) {{
              return '<p class="muted">Zapytanie nie zwróciło kolumn.</p>';
            }}
            const header = columns.map((column) => `<th>${{escapeHtml(String(column))}}</th>`).join('');
            const body = rows.map((row) => `<tr>${{row.map((cell) => `<td>${{escapeHtml(String(cell ?? 'NULL'))}}</td>`).join('')}}</tr>`).join('');
            return `<table><thead><tr>${{header}}</tr></thead><tbody>${{body}}</tbody></table>`;
          }}

          function escapeHtml(text) {{
            return text
              .replaceAll('&', '&amp;')
              .replaceAll('<', '&lt;')
              .replaceAll('>', '&gt;')
              .replaceAll('"', '&quot;')
              .replaceAll("'", '&#39;');
          }}

          window.runQuery = async function runQuery() {{
            const sql = editor.getValue().trim();
            if (!sql) {{
              statusEl.className = 'status error';
              statusEl.textContent = 'Zapytanie nie może być puste.';
              return;
            }}

            setLoading(true);
            resultArea.innerHTML = '';
            metaEl.textContent = '';

            try {{
              const response = await fetch('/execute', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{ lessonId: LESSON_CONTEXT.slug, sql }})
              }});
              const payload = await response.json();

              if (!response.ok) {{
                throw new Error(payload.detail || 'Nie udało się wykonać zapytania.');
              }}

              const hasError = Boolean(payload.error);
              statusEl.className = hasError ? 'status error' : 'status success';
              statusEl.textContent = hasError
                ? `Błąd: ${{payload.error}}`
                : `Ocena ćwiczenia: ${{payload.gradingStatus.toUpperCase()}} — ${{payload.feedback}}`;

              metaEl.textContent = `Czas wykonania: ${{payload.executionMs}} ms${{payload.truncated ? ' (wynik przycięty)' : ''}}`;
              resultArea.innerHTML = hasError ? '' : renderTable(payload.columns || [], payload.rows || []);
            }} catch (error) {{
              statusEl.className = 'status error';
              statusEl.textContent = `Błąd sieci: ${{error.message}}`;
            }} finally {{
              setLoading(false);
            }}
          }};

          runBtn.addEventListener('click', () => window.runQuery());
          resetBtn.addEventListener('click', () => {{
            editor.setValue(LESSON_CONTEXT.starterQuery);
            statusEl.className = 'status muted';
            statusEl.textContent = 'Zapytanie zresetowane do wartości startowej.';
            resultArea.innerHTML = '';
            metaEl.textContent = '';
          }});

          hintBtn.addEventListener('click', () => {{
            const hints = LESSON_CONTEXT.solutionHints || [];
            if (!hints.length) {{
              hintBox.hidden = false;
              hintBox.textContent = 'Brak podpowiedzi dla tej lekcji.';
              return;
            }}
            const existing = Number(hintBox.dataset.index || 0);
            const next = existing % hints.length;
            hintBox.hidden = false;
            hintBox.textContent = `Podpowiedź ${{next + 1}}/${{hints.length}}: ${{hints[next]}}`;
            hintBox.dataset.index = String(next + 1);
          }});
        </script>
        """,
        title=f"{lesson['title']} – Kurs SQL",
    )
    return HTMLResponse(content=html)


@app.post("/execute", response_model=ExecuteResponse)
def execute(request: ExecuteRequest) -> ExecuteResponse:
    try:
        result = runner.execute(lesson_id=request.lessonId, sql=request.sql)
        grade_result = grader.grade(lesson_id=request.lessonId, sql=request.sql, actual=result)
        return ExecuteResponse(
            columns=result.columns,
            rows=result.rows,
            executionMs=round(result.execution_ms, 3),
            error=result.error,
            truncated=result.truncated,
            gradingStatus=grade_result.status,
            feedback=grade_result.feedback,
        )
    except SqlValidationError as exc:
        return ExecuteResponse(
            columns=[],
            rows=[],
            executionMs=0.0,
            error=str(exc),
            truncated=False,
            gradingStatus="fail",
            feedback=f"❌ Zapytanie nie przeszło walidacji: {exc}",
        )
