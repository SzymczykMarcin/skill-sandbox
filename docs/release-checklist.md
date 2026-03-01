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
- [ ] Endpoint Prometheus `/metrics` zwraca metryki `sql_course_http_requests_total`, `sql_course_http_status_total`, `sql_course_http_429_total`, `sql_course_http_request_duration_seconds`, `sql_course_app_errors_total`.
- [ ] Integracja raportowania wyjątków aplikacyjnych jest aktywna (`SENTRY_DSN` ustawione albo świadoma decyzja o pozostaniu przy logach lokalnych).
- [ ] Błędy SQL (`sql_execution_error`) i wyjątki aplikacyjne (`execute_exception`, `unhandled_exception`) są widoczne w logach oraz metryce `sql_course_app_errors_total`.
- [ ] Dashboard używa histogramu `sql_course_http_request_duration_seconds` do p95 endpointu `/execute` i pokazuje oddzielnie liczniki 429.

## 4) Minimalne alerty (Prometheus)
- [ ] **Wzrost 5xx**: alert gdy `sum(rate(sql_course_http_status_total{status=~"5.."}[5m])) > 0.05` przez `10m`.
- [ ] **Wzrost 429**: alert gdy `sum(rate(sql_course_http_429_total[5m])) > 0.1` przez `10m`.
- [ ] **Degradacja p95 `/execute`**: alert gdy `histogram_quantile(0.95, sum by (le) (rate(sql_course_http_request_duration_seconds_bucket{path="/execute"}[5m]))) > 1.2` przez `15m`.
- [ ] Każdy alert ma zdefiniowany ownera dyżuru i kanał eskalacji (Slack/PagerDuty).
