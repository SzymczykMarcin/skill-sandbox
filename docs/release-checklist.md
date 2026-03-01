# Release checklist

## 1) Konfiguracja środowiska
- [ ] Ustawione wymagane zmienne środowiskowe (`SQLITE_RUNTIME_DIR`, `SQL_QUERY_TIMEOUT_S`, `SQL_MAX_ROWS`, limity `/execute`).
- [ ] Katalog runtime SQLite istnieje i ma prawa zapisu dla procesu aplikacji.
- [ ] Snapshot bazowy SQLite jest odtwarzalny z `db/schema.sql` i `db/seed.sql`.
- [ ] Sprawdzone uruchomienie aplikacji (`uvicorn backend.main:app`) oraz endpointów `/kurs/sql`, `/execute`, `/reset-db`.

## 2) Backup treści kursu
- [ ] Wykonany backup katalogu `content/sql-course` przed wdrożeniem.
- [ ] Zweryfikowana integralność backupu (suma kontrolna lub testowe odtworzenie).
- [ ] Sprawdzone, że nowe/zmienione lekcje przechodzą walidator (`scripts/validate_sql_course.py`).
- [ ] Potwierdzony plan rollbacku treści (jak i skąd przywracamy pliki JSON).

## 3) Monitoring błędów i metryk użycia
- [ ] Zbieranie logów błędów backendu jest włączone (szczególnie błędy wykonania `/execute`).
- [ ] Dostępny dashboard metryk użycia (liczba żądań `/execute`, błędy 4xx/5xx, limity 429, czas odpowiedzi).
- [ ] Ustawione alerty na wzrost błędów endpointu `/execute` oraz degradację czasu odpowiedzi.
- [ ] Zweryfikowane logowanie kluczowych zdarzeń release (start aplikacji, reset bazy, wyjątki krytyczne).
