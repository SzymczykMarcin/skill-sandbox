# skill-sandbox

## SQL course dataset

- Schemat bazy: `db/schema.sql`
- Dane startowe: `db/seed.sql`
- Skrypt resetu per sesja/uruchomienie: `./db/reset_session_db.sh [ścieżka_docelowa.sqlite]`

> Uwaga: nie trzymamy binarnych snapshotów SQLite w repozytorium.
> Snapshot bazowy jest tworzony warunkowo przy pierwszym uruchomieniu skryptu,
> domyślnie w katalogu runtime `.runtime/sqlite/base_snapshot.sqlite`.

Przykład resetu:

```bash
./db/reset_session_db.sh .runtime/sqlite/session.sqlite
```

Konfiguracja przez zmienne środowiskowe:

- `SQLITE_RUNTIME_DIR` – katalog runtime (domyślnie `.runtime/sqlite`)
- `SQLITE_BASE_DB_PATH` – pełna ścieżka do bazowego snapshotu

## Backend API (FastAPI)

Uruchomienie lokalne:

```bash
uvicorn backend.main:app --reload
```

Endpoint `POST /execute` przyjmuje payload:

```json
{
  "lessonId": "01-select-basics",
  "sql": "SELECT id, email FROM users"
}
```

I zwraca ustandaryzowany wynik:

- `columns`: nazwy kolumn,
- `rows`: zwrócone rekordy (maksymalnie `SQL_MAX_ROWS`, domyślnie 200),
- `executionMs`: czas wykonania,
- `error`: komunikat błędu (lub `null`),
- `truncated`: flaga przycięcia wyniku.

Zmienne środowiskowe backendu:

- `SQL_QUERY_TIMEOUT_S` – limit czasu wykonania pojedynczego zapytania (domyślnie `3`),
- `SQL_MAX_ROWS` – limit liczby zwracanych rekordów (domyślnie `200`).
