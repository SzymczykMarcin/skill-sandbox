# ADR 0001: FastAPI SSR jako architektura MVP

- Status: zaakceptowany
- Data: 2026-03-01

## Kontekst

W repozytorium działa już aplikacja FastAPI, która:
- renderuje strony kursu SQL po stronie serwera (`/kurs/sql`, `/kurs/sql/{slug}`),
- udostępnia endpointy JSON dla wykonania zapytań SQL,
- utrzymuje logikę kursu i wykonania SQL w jednym serwisie.

W dokumentacji architektury pojawiło się wcześniejsze założenie migracji do Next.js + TypeScript. To założenie nie odpowiada obecnemu stanowi kodu i zwiększałoby zakres prac poza MVP.

## Decyzja

Pozostajemy przy **SSR w FastAPI** jako docelowym wariancie dla MVP.

Nie wdrażamy osobnej aplikacji Next.js na obecnym etapie.

## Uzasadnienie

1. **Spójność ze stanem repozytorium** – aktualna implementacja działa już end-to-end w FastAPI.
2. **Niższa złożoność operacyjna** – jeden serwis, jeden pipeline uruchomieniowy i mniej punktów awarii.
3. **Szybsze dostarczenie MVP** – brak konieczności odtwarzania istniejących widoków w nowym stacku.
4. **Elastyczność na przyszłość** – endpointy JSON (`/lessons`, `/lessons/{slug}`, `/execute`) pozostają dostępne pod ewentualny frontend SPA.

## Konsekwencje

- Dokumentacja architektury musi opisywać FastAPI jako warstwę SSR + API.
- Rozwój funkcji MVP koncentruje się na backendzie i warstwie szablonów/renderingu HTML.
- Ewentualna migracja do oddzielnego frontendu zostaje odłożona do osobnej decyzji architektonicznej po MVP.
