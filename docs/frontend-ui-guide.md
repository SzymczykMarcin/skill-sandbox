# Frontend UI Guide

Ten dokument opisuje bazowe zasady projektowania interfejsu dla kursu SQL. Celem jest spójność wizualna, czytelność treści edukacyjnej i przewidywalne zachowanie komponentów.

## 1. Design tokens

### Kolory

Używaj semantycznych ról kolorów zamiast „surowych” nazw (`blue-500`, `gray-200`), np.:

- `color-bg-page` – tło całej strony,
- `color-bg-surface` – tło kart/sekcji,
- `color-text-primary` – główny tekst,
- `color-text-secondary` – tekst pomocniczy,
- `color-border-default` – obramowania,
- `color-brand-primary` – akcje główne,
- `color-feedback-success|warning|error|info` – statusy i komunikaty.

Zasady:

- Zachowaj kontrast minimum WCAG AA (4.5:1 dla tekstu podstawowego).
- Nie koduj znaczenia wyłącznie kolorem; dodawaj ikonę lub etykietę.
- Dla hover/focus używaj wariantów tej samej roli semantycznej.

### Spacing

Stosuj skalę odstępów opartą o krok 4 px:

- `space-1 = 4px`
- `space-2 = 8px`
- `space-3 = 12px`
- `space-4 = 16px`
- `space-6 = 24px`
- `space-8 = 32px`
- `space-10 = 40px`
- `space-12 = 48px`

Zasady:

- Wewnątrz komponentów trzymaj się małych kroków (`space-2` do `space-4`).
- Między sekcjami ekranu używaj większych kroków (`space-6` do `space-12`).
- Nie mieszaj przypadkowych wartości (np. 14px, 22px), jeśli token istnieje.

### Typografia

Minimalny zestaw ról tekstowych:

- `text-display` – duże nagłówki ekranu,
- `text-h1`, `text-h2`, `text-h3` – hierarchia nagłówków,
- `text-body` – główna treść,
- `text-body-sm` – treść pomocnicza,
- `text-caption` – podpisy i metadane,
- `text-code` – SQL i fragmenty techniczne.

Zasady:

- W treściach edukacyjnych preferuj `text-body` i wysoki line-height (1.5–1.7).
- Ogranicz liczbę różnych rozmiarów/font-weight na jednym ekranie.
- Nie używaj wielkich liter dla długich bloków tekstu.

## 2. Warianty przycisków

### Primary

- Najważniejsza akcja na ekranie (np. „Uruchom zapytanie”).
- Maksymalnie jeden primary per sekcja kontekstowa.

### Secondary

- Akcje wspierające (np. „Pokaż podpowiedź”, „Wróć”).
- Wizualnie lżejszy niż primary.

### Tertiary / Ghost

- Drobne akcje inline i w pomocniczych miejscach.
- Bez dominującego wypełnienia, ale z wyraźnym focus ring.

### Destructive

- Akcje nieodwracalne (np. „Wyczyść postęp”).
- Wymaga jasnego labela i opcjonalnego potwierdzenia.

### Rozmiary i stany

- Rozmiary: `sm`, `md`, `lg` (spójne wysokości i paddingi z tokenami spacing).
- Każdy wariant musi mieć stany: `default`, `hover`, `focus-visible`, `disabled`, `loading`.
- W stanie `loading` zachowaj stałą szerokość przycisku (spinner + etykieta lub stały placeholder).

## 3. Status badges

Badge służy do krótkiej informacji o stanie, np. „Ukończone”, „W trakcie”, „Nowe”, „Błąd”.

Zasady projektowe:

- Krótka treść (1–2 słowa).
- Stała wysokość i minimalna szerokość wynikająca z tokenów.
- Warianty semantyczne: `success`, `warning`, `error`, `info`, `neutral`.
- Badge nie zastępuje pełnego komunikatu błędu; tylko sygnalizuje stan.

Zasady użycia:

- Przy listach lekcji używaj badge do statusu postępu.
- W panelach wyników można dodać badge `error/success` jako szybki sygnał.
- Nie używaj kilku badge o podobnym znaczeniu obok siebie.

## 4. Do/Don’t dla treści edukacyjnej

### Do

- Pisz krótkie akapity: 2–4 zdania.
- Rozdzielaj teorię i praktykę nagłówkami oraz listami.
- Wyróżniaj kluczowe pojęcia **pogrubieniem** (oszczędnie).
- Używaj calloutów (`info`, `tip`, `warning`) dla kontekstu i pułapek.
- Dodawaj konkretne przykłady SQL blisko opisu reguły.

### Don’t

- Nie twórz ścian tekstu (powyżej 6–7 zdań bez przerwy).
- Nie nadużywaj wyróżnień (bold, caps, kolory jednocześnie).
- Nie ukrywaj kluczowych ograniczeń tylko w przypisach.
- Nie mieszaj wielu nowych pojęć w jednym akapicie bez przykładów.
- Nie używaj niejednoznacznych calloutów bez jasnego „co zrobić dalej”.

## 5. Definition of Done dla nowych ekranów

Nowy ekran frontendu uznajemy za gotowy, gdy spełnia poniższą checklistę:

- [ ] **Responsive:** poprawne działanie co najmniej dla mobile, tablet, desktop.
- [ ] **A11y:** pełna obsługa klawiatury, widoczny focus, poprawne role/labelki ARIA.
- [ ] **Kontrast:** tekst i komponenty spełniają minimum WCAG AA.
- [ ] **Stany danych:** zdefiniowane i zaimplementowane `loading`, `error`, `empty`, `success`.
- [ ] **Przyciski/akcje:** wszystkie akcje mają właściwe warianty i stany `disabled/loading`.
- [ ] **Komunikaty:** błędy i sukcesy są zrozumiałe i wskazują kolejne kroki.
- [ ] **Spójność tokenów:** kolory, spacing i typografia używają tokenów zamiast wartości ad hoc.
- [ ] **Treść edukacyjna:** sekcje są krótkie, czytelne i zawierają praktyczne przykłady.
- [ ] **QA ręczne:** przejście scenariusza happy path + co najmniej jednego błędu.
