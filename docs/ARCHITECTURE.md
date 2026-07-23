# Architecture — PoroPilot

## Overview

```
  Browser
    │
    ▼
  Vue 3 SPA (Vite)                     frontend/
    │  fetch (services/api.js)
    ▼
  FastAPI  (async)                     backend/app/
    ├── api/routes.py    thin routes, Pydantic in/out
    ├── dependencies.py  injects the Riot client
    ├── riot/client.py   Riot API calls + region routing + caching
    ├── ai/draft.py      Claude draft assistant (structured output)
    ├── cache.py         in-memory TTL cache (swap for Redis in prod)
    └── main.py          app wiring + lifespan (pooled httpx client)
    │
    ├──────────────▶ Riot Games API   (profile, rank, mastery, matches)
    ├──────────────▶ Data Dragon CDN  (static champion data + images)
    └──────────────▶ Anthropic API    (draft help, patch digest)
```

## Components

| Layer | Tech | Responsibility |
|---|---|---|
| Frontend | Vue 3, Vite, Pinia | UI, state, calls the backend only |
| Backend | FastAPI, httpx, Pydantic | Riot/Data Dragon/AI orchestration, caching |
| Cache | in-memory TTL (Redis in prod) | Protect the rate-limited Riot API |
| AI | Anthropic Claude API | Draft suggestions, patch summaries |

## Request flow (summoner lookup)

1. The Vue `useSummoner` composable debounces input and calls
   `GET /api/summoner/{region}/{name}/{tag}`, caching results client-side.
2. FastAPI injects a `RiotClient` (wrapping the shared pooled `httpx` client).
3. `load_profile` resolves Riot ID → PUUID (Account-V1), then fetches Summoner,
   League and Champion-Mastery data, each cached server-side by TTL.
4. A validated `Profile` (Pydantic) is returned as JSON.

## Configuration

All via environment / `backend/.env` (see `backend/.env.example`):

| Var | Purpose |
|---|---|
| `RIOT_API_KEY` | Riot developer key |
| `ANTHROPIC_API_KEY` | Claude API key |
| `ANTHROPIC_MODEL` | Which Claude model the AI features use |
| `REDIS_URL` | Optional; falls back to in-memory cache |

## Running locally

```bash
cp backend/.env.example backend/.env   # fill in keys
docker compose up --build              # frontend :5173, backend :8000/docs
```

Or run each part directly — see `CLAUDE.md` → Commands.

## Testing

- **Backend:** `python -m unittest discover` (unit tests, no network).
- **Frontend:** `npx playwright test` (end-to-end against the dev server).
- Both run in CI on every push/PR (`.github/workflows/ci.yml`).

## Deployment (planned)

- Build the backend and frontend Docker images.
- Host on a **DigitalOcean droplet** running the images via Docker Compose,
  behind **Nginx** (TLS + reverse proxy) with **Gunicorn/uvicorn** workers.
- CI deploy step (currently commented in `ci.yml`): on merge to `main`, push the
  images and SSH to the droplet to pull and restart. Secrets live in GitHub
  Actions secrets, never in the repo.
- Swap the in-memory cache for **Redis** before running more than one worker.
