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
