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


## Szybki start na Windows 11 (jeden plik)

W katalogu repo jest skrypt `start.ps1`, który:
- znajdzie Python 3,
- utworzy `.venv` (jeśli nie istnieje),
- doinstaluje brakujące biblioteki,
- uruchomi gotową stronę kursu.

Uruchom w PowerShell (w katalogu repo):

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\start.ps1
```

Po starcie otwórz: `http://127.0.0.1:8000/kurs/sql`

Przydatne opcje:

```powershell
.\start.ps1 -Port 8080
.\start.ps1 -BindHost 0.0.0.0 -NoReload
.\start.ps1 -SkipVenv
```


## Frontend

- Przewodnik UI (tokeny, komponenty, zasady treści, DoD): `docs/frontend-ui-guide.md`

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
- `truncated`: flaga przycięcia wyniku,
- `gradingStatus`: `pass` lub `fail` po walidacji ćwiczenia,
- `feedback`: czytelny komunikat po polsku z oceną rozwiązania.

Każda lekcja ma teraz sekcję `validation` z:
- zapytaniem wzorcowym (`expectedSql`),
- regułami porównania (`ignoreRowOrder`, `ignoreColumnOrder`, `numericTolerance`),
- opcjonalnymi wymaganiami semantycznymi (`requiredClauses`, np. `JOIN`, `GROUP BY`).

Zmienne środowiskowe backendu:

- `SQL_QUERY_TIMEOUT_S` – limit czasu wykonania pojedynczego zapytania (domyślnie `3`),
- `SQL_MAX_ROWS` – limit liczby zwracanych rekordów (domyślnie `200`),
- `EXECUTE_RATE_LIMIT_MAX_REQUESTS` – maksymalna liczba żądań w oknie (domyślnie `20`),
- `EXECUTE_RATE_LIMIT_WINDOW_S` – długość okna limitu (domyślnie `60` sekund),
- `APP_ENV` – środowisko uruchomieniowe (`development`/`production`); domyślnie `development`,
- `EXECUTE_RATE_LIMIT_BACKEND` – backend limitera (`memory` albo `redis`); domyślnie `redis` dla `APP_ENV=production`, w innych przypadkach `memory`,
- `EXECUTE_RATE_LIMIT_REDIS_URL` – URL Redis używany przez limiter (domyślnie `redis://localhost:6379/0`),
- `EXECUTE_RATE_LIMIT_REDIS_PREFIX` – prefiks kluczy limitera w Redis (domyślnie `execute`),
- `EXECUTE_RATE_LIMIT_INCLUDE_IP` – czy klucz limitu ma zawierać IP klienta (domyślnie `true`),
- `EXECUTE_RATE_LIMIT_INCLUDE_SESSION` – czy klucz limitu ma zawierać identyfikator sesji (domyślnie `false`),
- `EXECUTE_RATE_LIMIT_INCLUDE_USER` – czy klucz limitu ma zawierać identyfikator użytkownika (domyślnie `false`),
- `EXECUTE_RATE_LIMIT_SESSION_HEADER` – nazwa nagłówka sesji (domyślnie `X-Session-Id`),
- `EXECUTE_RATE_LIMIT_USER_HEADER` – nazwa nagłówka użytkownika (domyślnie `X-User-Id`).

W trybie developerskim domyślnie używany jest limiter in-memory. W środowisku produkcyjnym (`APP_ENV=production`) backend domyślnie przełącza się na Redis, dzięki czemu limit działa poprawnie przy wielu instancjach aplikacji.
