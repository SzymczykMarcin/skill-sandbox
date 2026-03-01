# Architektura MVP – platforma lekcji SQL

## 1. Decyzja technologiczna

### Warstwa web (SSR + API)
- **FastAPI (Python) + renderowanie HTML po stronie serwera (SSR)**
- Uzasadnienie:
  - obecna aplikacja już dostarcza kompletne widoki kursu (`/kurs/sql`, `/kurs/sql/{slug}`),
  - jeden runtime upraszcza utrzymanie MVP (routing, API i widoki w tym samym serwisie),
  - brak dodatkowego frontendu redukuje koszt wdrożenia i utrzymania.

### API JSON
- **Endpointy REST w FastAPI**
- Uzasadnienie:
  - czytelny kontrakt danych i łatwa walidacja wejścia/wyjścia,
  - możliwość ponownego użycia tych samych danych przez przyszły frontend SPA,
  - szybka implementacja i automatyczna dokumentacja OpenAPI.

### Silnik SQL
- **SQLite** uruchamiany w trybie **izolowanym per sesja**.
- Uzasadnienie:
  - najprostszy start i brak zewnętrznej infrastruktury,
  - możliwość szybkiego tworzenia tymczasowych baz dla użytkownika/sesji,
  - dobre dopasowanie do ćwiczeń edukacyjnych (deterministyczne środowisko).

---

## 2. Przepływ danych

### `GET /kurs/sql` (SSR)
1. Przeglądarka żąda strony spisu lekcji.
2. FastAPI ładuje lekcje z plików `content/sql-course/*.json`.
3. Serwer renderuje HTML listy lekcji i zwraca gotowy dokument.
4. Po stronie przeglądarki aktualizowany jest status postępu (localStorage).

### `GET /kurs/sql/{slug}` (SSR)
1. Przeglądarka żąda strony konkretnej lekcji.
2. FastAPI ładuje wskazaną lekcję oraz wyznacza poprzednią/następną.
3. Serwer renderuje HTML z treścią lekcji, nawigacją i osadzonym playgroundem SQL.
4. Klient uruchamia skrypt edytora i przywraca szkic zapytania użytkownika z localStorage.

### `POST /execute` (JSON)
1. Skrypt strony lekcji wysyła zapytanie SQL wraz z identyfikatorem lekcji.
2. Backend:
   - tworzy lub pobiera izolowaną bazę SQLite dla sesji,
   - waliduje zapytanie pod kątem reguł bezpieczeństwa,
   - wykonuje zapytanie z limitami.
3. Backend zwraca JSON ze statusem (`ok`/`error`) oraz wynikiem lub błędem.
4. Strona SSR aktualizuje tabelę wyników i metadane wykonania bez przeładowania.

---

## 3. Wymagania niefunkcjonalne

### Limit czasu zapytania
- Każde wykonanie SQL musi mieć **twardy timeout** (np. 2 sekundy).
- Po przekroczeniu limitu backend przerywa wykonanie i zwraca kontrolowany błąd.

### Limit zwracanych wierszy
- Wynik musi być ograniczony do maksymalnej liczby rekordów (np. 100).
- Gdy wynik jest większy, API zwraca tylko pierwszy fragment oraz flagę `truncated=true`.

### Blokady komend niebezpiecznych
- Dla MVP dozwolone są głównie zapytania odczytowe (`SELECT`, opcjonalnie `WITH`).
- Należy blokować co najmniej:
  - `DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `ATTACH`, `DETACH`,
  - wielokrotne statementy rozdzielone `;`.
- Walidacja musi zachodzić po stronie backendu, niezależnie od frontendu.

---

## 4. Kryteria MVP (end-to-end)

MVP jest ukończone, gdy działają wszystkie elementy poniżej:

1. Użytkownik widzi listę lekcji pod `/kurs/sql`.
2. Użytkownik otwiera lekcję pod `/kurs/sql/{slug}` i widzi:
   - treść,
   - instrukcję ćwiczenia,
   - pole do wpisania SQL.
3. Użytkownik wysyła zapytanie przez `POST /execute`.
4. Backend uruchamia zapytanie na izolowanej bazie SQLite per sesja.
5. Użytkownik otrzymuje poprawny wynik tabeli albo czytelny błąd walidacji/wykonania.
6. Limity niefunkcjonalne (timeout, max rows, blokada niebezpiecznych komend) są egzekwowane.

To zapewnia pełny, minimalny przepływ „od wyboru lekcji do wykonania SQL i wyświetlenia wyniku”.
