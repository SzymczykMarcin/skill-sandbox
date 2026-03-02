(() => {
  const LESSON_CONTEXT = window.LESSON_CONTEXT;
  const { loadProgress, updateProgress } = window.SQLCourseProgress;

  class SqlEditor {
    constructor(container, initialValue, onChange) {
      this.container = container;
      this.initialValue = initialValue;
      this.onChange = onChange;
      this.fallback = null;
      this.view = null;
    }

    async mount() {
      try {
        await this._mountCodeMirror();
      } catch (_error) {
        this._mountFallback();
      }
    }

    async _mountCodeMirror() {
      const [cmView, cmState, cmCommands, cmSql] = await Promise.all([
        import('https://esm.sh/@codemirror/view@6.36.2'),
        import('https://esm.sh/@codemirror/state@6.5.0'),
        import('https://esm.sh/@codemirror/commands@6.8.1'),
        import('https://esm.sh/@codemirror/lang-sql@6.10.0'),
      ]);

      const customTheme = cmView.EditorView.theme({
        '&': {
          minHeight: '220px',
          fontFamily: 'Menlo, Consolas, monospace',
          fontSize: '14px',
          color: 'var(--color-text)',
          backgroundColor: 'var(--color-surface-elevated)',
        },
        '.cm-gutters': {
          backgroundColor: 'var(--color-surface-subtle)',
          color: 'var(--color-text-meta)',
          borderRight: '1px solid var(--color-border-soft)',
        },
        '.cm-activeLine, .cm-activeLineGutter': {
          backgroundColor: 'var(--color-surface-muted)',
        },
        '.cm-cursor, .cm-dropCursor': { borderLeftColor: 'var(--color-text)' },
        '.cm-selectionBackground, ::selection': { backgroundColor: 'var(--color-primary-soft)' },
        '.cm-content': { minHeight: '220px' },
      });

      const onRunShortcut = cmView.keymap.of([
        {
          key: 'Mod-Enter',
          run: () => {
            window.runQuery();
            return true;
          },
        },
        ...cmCommands.defaultKeymap,
      ]);

      const onChange = cmView.EditorView.updateListener.of((update) => {
        if (!update.docChanged) {
          return;
        }
        this.onChange?.(update.state.doc.toString());
      });

      const state = cmState.EditorState.create({
        doc: this.initialValue,
        extensions: [
          cmView.keymap.of(cmCommands.defaultKeymap),
          onRunShortcut,
          cmSql.sql({ upperCaseKeywords: true }),
          cmView.EditorView.lineWrapping,
          onChange,
          customTheme,
        ],
      });

      this.view = new cmView.EditorView({ state, parent: this.container });
    }

    _mountFallback() {
      const textarea = document.createElement('textarea');
      textarea.className = 'editor-fallback';
      textarea.value = this.initialValue;
      textarea.addEventListener('keydown', (event) => {
        if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
          event.preventDefault();
          window.runQuery();
        }
      });
      textarea.addEventListener('input', () => this.onChange?.(textarea.value));
      this.container.innerHTML = '';
      this.container.append(textarea);
      this.fallback = textarea;
    }

    getValue() {
      if (this.view) {
        return this.view.state.doc.toString();
      }
      return this.fallback ? this.fallback.value : '';
    }

    setValue(value) {
      if (this.view) {
        const transaction = this.view.state.update({
          changes: { from: 0, to: this.view.state.doc.length, insert: value },
        });
        this.view.dispatch(transaction);
        this.view.focus();
        this.onChange?.(value);
        return;
      }
      if (this.fallback) {
        this.fallback.value = value;
        this.fallback.focus();
        this.onChange?.(value);
      }
    }
  }

  const statusEl = document.getElementById('query-status');
  const metaEl = document.getElementById('result-meta');
  const resultArea = document.getElementById('result-area');
  const runBtn = document.getElementById('run-query');
  const resetBtn = document.getElementById('reset-query');
  const hintBtn = document.getElementById('show-hint');
  const hintBox = document.getElementById('hint-box');
  const toastRegion = document.getElementById('toast-region');
  let toastTimer = null;

  const savedProgress = loadProgress();
  const restoredSql =
    typeof savedProgress.lessonDrafts?.[LESSON_CONTEXT.slug] === 'string'
      ? savedProgress.lessonDrafts[LESSON_CONTEXT.slug]
      : LESSON_CONTEXT.starterQuery;

  const editor = new SqlEditor(document.getElementById('sql-editor'), restoredSql, (sql) =>
    updateProgress((progress) => {
      progress.lessonDrafts = progress.lessonDrafts || {};
      progress.startedLessons = progress.startedLessons || {};
      progress.lessonDrafts[LESSON_CONTEXT.slug] = sql;
      progress.startedLessons[LESSON_CONTEXT.slug] = true;
      progress.lastVisitedLesson = LESSON_CONTEXT.slug;
    })
  );
  editor.mount();

  updateProgress((progress) => {
    progress.startedLessons = progress.startedLessons || {};
    progress.startedLessons[LESSON_CONTEXT.slug] = true;
    progress.lastVisitedLesson = LESSON_CONTEXT.slug;
  });


  function announceStatus(message, tone = 'polite', toneClass = 'muted') {
    statusEl.className = `status ${toneClass}`;
    statusEl.setAttribute('aria-live', tone);
    statusEl.textContent = message;
  }

  function setLoading(loading) {
    runBtn.disabled = loading;
    resetBtn.disabled = loading;
    runBtn.classList.toggle('is-loading', loading);
    const runLabel = runBtn.querySelector('.btn-label');
    if (runLabel) {
      runLabel.textContent = loading ? 'Wykonywanie…' : 'Uruchom zapytanie';
    }
    if (loading) {
      announceStatus('Wykonywanie zapytania...', 'polite', 'loading');
    }
  }

  function showToast(message, variant = 'info') {
    if (!toastRegion) {
      return;
    }
    window.clearTimeout(toastTimer);
    toastRegion.textContent = message;
    toastRegion.className = `toast-region is-visible ${variant}`;
    toastTimer = window.setTimeout(() => {
      toastRegion.className = 'toast-region';
      toastRegion.textContent = '';
    }, 2600);
  }

  function renderEmptyState(title, description) {
    return `<section class="empty-state"><h3>${escapeHtml(title)}</h3><p class="muted">${escapeHtml(description)}</p></section>`;
  }

  function renderErrorPanel(message, details) {
    return `<section class="error-panel"><h3>Błąd wykonania zapytania</h3><p>${escapeHtml(message)}</p><p class="muted">${escapeHtml(details)}</p></section>`;
  }

  function renderTable(columns, rows) {
    if (!columns.length) {
      return renderEmptyState('Brak kolumn w wyniku', 'Zapytanie wykonało się poprawnie, ale nie zwróciło żadnych nazwanych kolumn.');
    }
    if (!rows.length) {
      return renderEmptyState('Brak rekordów', 'Zapytanie nie zwróciło żadnych danych dla podanych warunków.');
    }
    const header = columns.map((column) => `<th>${escapeHtml(String(column))}</th>`).join('');
    const body = rows
      .map((row) => `<tr>${row.map((cell) => `<td>${escapeHtml(String(cell ?? 'NULL'))}</td>`).join('')}</tr>`)
      .join('');
    return `<div class="result-table-wrap"><table><thead><tr>${header}</tr></thead><tbody>${body}</tbody></table></div>`;
  }

  function escapeHtml(text) {
    return text
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;')
      .replaceAll("'", '&#39;');
  }

  window.runQuery = async function runQuery() {
    const sql = editor.getValue().trim();
    if (!sql) {
      announceStatus('Zapytanie nie może być puste.', 'assertive', 'error');
      return;
    }

    setLoading(true);
    resultArea.innerHTML = '';
    metaEl.textContent = '';

    try {
      const response = await fetch('/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ lessonId: LESSON_CONTEXT.slug, sql }),
      });
      const payload = await response.json();

      if (!response.ok) {
        throw new Error(payload.detail || 'Nie udało się wykonać zapytania.');
      }

      const hasError = Boolean(payload.error);
      announceStatus(
        hasError
          ? `Błąd: ${payload.error}`
          : `Ocena ćwiczenia: ${payload.gradingStatus.toUpperCase()} — ${payload.feedback}`,
        hasError ? 'assertive' : 'polite',
        hasError ? 'error' : 'success'
      );

      if (!hasError && payload.gradingStatus === 'pass') {
        updateProgress((progress) => {
          progress.completedLessons = progress.completedLessons || {};
          progress.startedLessons = progress.startedLessons || {};
          progress.completedLessons[LESSON_CONTEXT.slug] = true;
          progress.startedLessons[LESSON_CONTEXT.slug] = true;
          progress.lastVisitedLesson = LESSON_CONTEXT.slug;
        });
        showToast('Świetnie! Lekcja została ukończona.', 'success');
      }

      const rowCount = Array.isArray(payload.rows) ? payload.rows.length : 0;
      const truncateLabel = payload.truncated ? 'Tak' : 'Nie';
      metaEl.innerHTML = [
        `<span><strong>Czas:</strong> ${payload.executionMs} ms</span>`,
        `<span><strong>Przycięcie:</strong> ${truncateLabel}</span>`,
        `<span><strong>Rekordy:</strong> ${rowCount}</span>`,
      ].join(' · ');
      resultArea.innerHTML = hasError
        ? renderErrorPanel(payload.error || 'Wystąpił błąd SQL.', 'Sprawdź składnię zapytania i spróbuj ponownie.')
        : renderTable(payload.columns || [], payload.rows || []);

      if (!hasError && payload.gradingStatus !== 'pass') {
        showToast('Postęp zapisany. Pracuj dalej nad rozwiązaniem.', 'info');
      }
    } catch (error) {
      announceStatus(`Błąd sieci: ${error.message}`, 'assertive', 'error');
      resultArea.innerHTML = renderErrorPanel('Nie udało się połączyć z serwerem.', error.message || 'Sprawdź połączenie sieciowe i ponów próbę.');
      showToast('Nie udało się wykonać zapytania.', 'error');
    } finally {
      setLoading(false);
    }
  };

  runBtn.addEventListener('click', () => window.runQuery());
  resetBtn.addEventListener('click', () => {
    editor.setValue(LESSON_CONTEXT.starterQuery);
    announceStatus('Zapytanie zresetowane do wartości startowej.', 'polite', 'muted');
    resultArea.innerHTML = '';
    metaEl.textContent = '';
    showToast('Przywrócono startową treść zapytania.', 'info');
  });

  hintBtn.addEventListener('click', () => {
    const hints = LESSON_CONTEXT.solutionHints || [];
    if (!hints.length) {
      hintBox.hidden = false;
      hintBox.textContent = 'Brak podpowiedzi dla tej lekcji.';
      return;
    }
    if (hintBox.hidden) {
      hintBox.hidden = false;
      hintBox.innerHTML = "<div class='hint-box-header'><strong>Podpowiedzi</strong><button id='hide-hint' class='btn btn-ghost btn-small' type='button'>Ukryj podpowiedź</button></div><ol class='hint-list'></ol>";
      hintBox.dataset.index = '0';
      hintBox.querySelector('#hide-hint')?.addEventListener('click', () => {
        hintBox.hidden = true;
        showToast('Podpowiedź została ukryta.', 'info');
      });
    }
    const existing = Number(hintBox.dataset.index || 0);
    const next = existing % hints.length;
    const hintList = hintBox.querySelector('.hint-list');
    if (hintList) {
      const listItem = document.createElement('li');
      listItem.textContent = hints[next];
      hintList.append(listItem);
    }
    hintBox.dataset.index = String(next + 1);
    showToast(`Wyświetlono podpowiedź ${next + 1}/${hints.length}.`, 'info');
  });
})();
