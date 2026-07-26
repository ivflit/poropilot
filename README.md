# PoroPilot 🐾

A League of Legends companion web app. Enter your **region + Riot ID** (`name#tag`) and PoroPilot loads
your profile, ranked stats and champion pool, highlights your strongest champs, summarises the latest
patch for the champs you play, and includes an **AI draft assistant** that recommends a pick from your
pool based on your role, allied picks and enemy bans.

> Portfolio project demonstrating full-stack development (Vue + FastAPI), external API integration,
> AI pipelines (Claude), automated testing and CI/CD.

![CI](https://github.com/ivflit/poropilot/actions/workflows/ci.yml/badge.svg)

<!-- Add once deployed: **Live demo:** https://poropilot.example.com -->


## Stack

- **Frontend:** Vue 3 + Vite (Pinia, Vue Router)
- **Backend:** FastAPI (async), httpx
- **AI:** Anthropic Claude API (draft assistant + patch digest)
- **Cache:** in-memory TTL cache (swap for Redis in prod)
- **Infra:** Docker Compose, GitHub Actions CI/CD

## Quick start

```bash
# 1. Backend env
cp backend/.env.example backend/.env   # add your RIOT_API_KEY and ANTHROPIC_API_KEY

# 2. Run everything
docker compose up --build

# Frontend → http://localhost:5173
# Backend  → http://localhost:8000/docs
```

Or run the backend on its own:

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Tests

```bash
cd backend && python -m unittest discover        # backend unit tests
cd frontend && npx playwright test                # frontend e2e
```

## Data sources

- **Riot Games API** — Account-V1, Summoner-V4, League-V4, Champion-Mastery-V4, Match-V5. Requires a
  (free) developer key from https://developer.riotgames.com.
- **Data Dragon** — static champion/item data + images (no key).

**Note:** patch notes and live "meta strength" aren't in the Riot API — PoroPilot derives champion
strength from your own mastery + recent win-rates, and uses the AI pipeline (web search + Claude) for
patch summaries. See `PROJECT.md` (the build plan) for detail.

## Deployment

Two supported paths, both documented in [`deploy/README.md`](deploy/README.md):

- **Free (recommended for the demo)** — frontend on **Netlify** (`netlify.toml`),
  backend + Redis on **Render**'s free tier (`render.yaml`). Both auto-deploy on push
  to `main`; no server, domain or TLS setup needed.
- **Own the box** — a single DigitalOcean droplet running Docker Compose behind Nginx
  (TLS), deployed over SSH by GitHub Actions on every push to `main`.

## ⚠️ Never commit your API keys — they live in `backend/.env` (gitignored).

---

*PoroPilot isn't endorsed by Riot Games and doesn't reflect the views of Riot Games or anyone officially
involved in producing or managing League of Legends.*
