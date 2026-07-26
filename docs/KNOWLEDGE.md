# PoroPilot — Project Knowledge

The single condensed reference for the project: what it is, how it's built, the
decisions behind it, the conventions, and the hard-won gotchas. Start here, then
see `ARCHITECTURE.md` (diagrams) and `../CLAUDE.md` (working rules).

## 1. What it is

A League of Legends companion web app. Enter a region + Riot ID (`name#tag`) to see
a summoner's profile, ranked standing, champion mastery and recent-form win-rates,
plus an **AI draft assistant** that recommends champion picks (from your pool and
strong out-of-pool options) given role, allied picks, enemy bans and enemy picks.
It's a portfolio project — code quality and polish matter as much as features.

## 2. Architecture at a glance

```
Vue 3 SPA (Vite)  ──HTTP──▶  FastAPI (async)  ──▶  Riot API + Data Dragon + AI (Claude/Gemini)
                                     └── cache (in-memory or Redis)
```

- **Frontend** `frontend/` — Vue 3 `<script setup>`, composables for logic, a
  services layer (`services/api.js`), SCSS with a CSS-custom-property token system
  (light/dark). Two-column dashboard UI.
- **Backend** `backend/app/` — FastAPI. Thin routers (`api/routes.py`), Pydantic
  schemas (`schemas.py`), dependency injection (`dependencies.py`), a pooled httpx
  client created in the app lifespan (`main.py`), and services under `riot/` and `ai/`.
- **AI** is provider-agnostic: `ai/provider.py` dispatches to `ai/draft.py`+`ai/patch.py`
  (Anthropic) or `ai/gemini.py` (Gemini) based on `AI_PROVIDER`/keys.
- **Cache** `cache.py` — async `get/set`; in-memory by default, Redis when `REDIS_URL` set.

## 3. Key decisions (and why)

- **FastAPI over Django** — the app is I/O-bound (many concurrent Riot calls); async fits.
- **Champion strength from the player's own data**, not a scraped tier list (no official
  meta API; scraping third parties risks their terms). Recent form uses mastery + a
  **Wilson lower-bound** score so small samples don't dominate.
- **Champion images are hot-linked from Data Dragon** (Riot's CDN); the backend only
  fetches the lightweight metadata (names, image filenames, patch version) once and caches it.
- **AI is optional and provider-switchable.** No key → AI features cleanly switch off
  (endpoints 503, UI hides the draft board). Gemini has a free tier for a live deploy.
- **Absolute imports** throughout the backend (`from app.x import y`) for consistency and
  move-safety; ruff enforces import order (`app` is first-party).

## 4. Data flows

- **Profile** `GET /api/summoner/{region}/{name}/{tag}` → Account-V1 (name#tag→PUUID) →
  Summoner-V4 (level/icon) → **League-V4 by-PUUID** (rank) → Champion-Mastery-V4.
- **Champion pool** `analyse_champion_pool` → Match-V5 (paged ids + concurrent detail
  under a semaphore) → per-champion aggregation → top champions by form score.
- **Draft** `POST /api/draft` and **patch digest** `GET /api/patch-digest` → the active
  AI provider, returning structured JSON.
- **Champions** `GET /api/champions` (id→name/icon map) and **config** `GET /api/config`
  (`ai_enabled` + `ddragon_version`) — both cached; version populated at startup.

## 5. Conventions

- Load the **fastapi-python** / **vue3-frontend** skills before writing that code.
- Backend: Pydantic in/out, DI, pooled httpx, thin routers, guard clauses.
- Frontend: `<script setup>`, composables, services layer, SCSS tokens (never hard-code
  colours — use `var(--…)`), light + dark must both work.
- **Tests must keep the hooks they rely on** (aria-labels: Region/Riot ID; class names:
  `.profile`, `.pool`, `.suggestions`, `.chip`; button text: "Suggest a pick").

## 6. Dev workflow

**Issue-first → `feature/<issue-number>-name` branch → PR → merge to `main` on green CI.**
`main` is branch-protected (requires the `backend` and `frontend` checks). Squash-merge,
delete the branch. See `../CLAUDE.md` for the full loop and the tasks list in `../tasks.md`.

## 7. Commands

```bash
docker compose up --build                 # whole app (frontend :5173, backend :8000/docs)
cd backend && python -m unittest discover # backend tests
cd frontend && npx playwright test        # e2e (stop the docker frontend first — see gotchas)
```

## 8. Gotchas we hit (don't relearn these the hard way)

- **Playwright reuses whatever is on `:5173`.** The Docker frontend serves that port, so
  e2e can run against *stale* code. Stop the docker frontend before running Playwright.
- **Docker won't pick up code/env changes on a plain `up`.** Use
  `docker compose up -d --build --force-recreate <svc>`.
- **Riot Summoner-V4 no longer returns an encrypted `id`.** Look up League entries
  **by PUUID** (`/lol/league/v4/entries/by-puuid/{puuid}`), not by summoner id.
- **An unhandled 500 has no CORS header**, so the browser shows it as "Failed to fetch"
  — a real backend error can masquerade as a CORS/network error. Check the backend logs.
- **`google-genai` needs a native build** that some local machines lack; CI (Linux) is the
  source of truth for the Gemini-dependent tests.
- **AI clients are built lazily** (never at import) so the app starts with no key.

## 9. Status

T1–T6, T8–T15 done (profile, champ pool via Ralph, draft assistant, AI patch digest,
Gemini backend, searchable icon pickers, two-column themed UI, etc.). **T7 (production
deploy) is the main open task.** Full backlog: `../tasks.md`.
