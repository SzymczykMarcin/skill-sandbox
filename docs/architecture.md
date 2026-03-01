# Architektura MVP – platforma lekcji SQL

## 1. Decyzja technologiczna

### Frontend
- **Next.js + TypeScript**
- Uzasadnienie:
  - szybkie budowanie interfejsu (routing, SSR/SSG, API routes opcjonalnie),
  - silne typowanie i łatwiejsze utrzymanie kodu,
  - duży ekosystem komponentów i narzędzi.

### Backend API
- **FastAPI (Python)**
- Uzasadnienie:
  - wysoka wydajność dla prostych endpointów REST,
  - czytelna deklaracja kontraktów danych (Pydantic),
  - szybka implementacja i łatwa dokumentacja OpenAPI.

### Silnik SQL
- **SQLite** uruchamiany w trybie **izolowanym per sesja**.
- Uzasadnienie:
  - najprostszy start i brak zewnętrznej infrastruktury,
  - możliwość szybkiego tworzenia tymczasowych baz dla użytkownika/sesji,
  - dobre dopasowanie do ćwiczeń edukacyjnych (deterministyczne środowisko).

---

## 2. Przepływ danych

### `GET /lessons`
1. Frontend wysyła żądanie do backendu.
2. Backend pobiera listę lekcji z warstwy danych (np. pliki JSON/MD lub tabela `lessons`).
3. Backend zwraca listę skróconych rekordów (np. `slug`, `title`, `difficulty`, `shortDescription`).
4. Frontend renderuje listę lekcji.

### `GET /lessons/:slug`
1. Frontend żąda konkretnej lekcji po `slug`.
2. Backend ładuje treść lekcji i metadane ćwiczenia:
   - opis zadania,
   - schema startowa,
   - przykładowe dane,
   - oczekiwany format wyniku.
3. Backend zwraca pełny obiekt lekcji.
4. Frontend renderuje treść i edytor SQL.

### `POST /execute`
1. Frontend wysyła zapytanie SQL wraz z identyfikatorem lekcji/sesji.
2. Backend:
   - tworzy lub pobiera izolowaną bazę SQLite dla sesji,
   - waliduje zapytanie pod kątem reguł bezpieczeństwa,
   - wykonuje zapytanie z limitami.
3. Backend zwraca:
   - status (`ok`/`error`),
   - wynik (`columns`, `rows`) albo komunikat błędu,
   - metadane wykonania (np. czas, liczba wierszy).
4. Frontend prezentuje wynik tabelarycznie lub błąd.

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

1. Użytkownik widzi listę lekcji z `GET /lessons`.
2. Użytkownik otwiera lekcję (`GET /lessons/:slug`) i widzi:
   - treść,
   - instrukcję ćwiczenia,
   - pole do wpisania SQL.
3. Użytkownik wysyła zapytanie przez `POST /execute`.
4. Backend uruchamia zapytanie na izolowanej bazie SQLite per sesja.
5. Użytkownik otrzymuje poprawny wynik tabeli albo czytelny błąd walidacji/wykonania.
6. Limity niefunkcjonalne (timeout, max rows, blokada niebezpiecznych komend) są egzekwowane.

To zapewnia pełny, minimalny przepływ „od wyboru lekcji do wykonania SQL i wyświetlenia wyniku”.
