# Tasks — PoroPilot backlog

Each task has a priority (p1 highest), dependencies, a Ralph flag (only big,
complex tasks use the `ralph.sh` loop — see `CLAUDE.md`), and acceptance criteria.
Tick a box only when the work is done **and** a test proves it.

## Order of play

```
T1 (champion data)  ── blocks ──▶ T2, T3, T4
T3 (pool + winrate) ── blocks ──▶ T5
T2, T4              ── blocks ──▶ T7 (deploy)
T6 (Redis)          independent
```

Do **T1 first** — it's unblocked and everything visual depends on it.

---

### T1 — Champion static-data service (Data Dragon)
- **Priority:** p1 · **Area:** backend · **Depends on:** — · **Ralph:** no
- **Why:** Riot returns numeric champion IDs; we need names and icons to show
  anything readable, and every other feature needs this mapping.
- **Acceptance criteria**
  - [x] Backend fetches and caches the current Data Dragon version on startup.
  - [x] A service maps `championId` → `{name, title, imageUrl}`.
  - [x] `GET /api/champions` returns the full mapping.
  - [x] Data is cached (no Data Dragon call per request).
  - [x] Unit tests cover the ID→name mapping with a stubbed dataset.

### T2 — Show champion names and icons in the profile
- **Priority:** p1 · **Area:** frontend · **Depends on:** T1 · **Ralph:** no
- **Why:** The profile currently shows "Champion 157" — unusable.
- **Acceptance criteria**
  - [x] Mastery list shows champion name + icon, not the raw ID.
  - [x] Ranked tier/rank/LP is rendered clearly.
  - [x] Graceful empty state for unranked players.
  - [x] Playwright test covers a rendered profile (mocked API).

### T3 — Champion pool and win-rate analysis
- **Priority:** p1 · **Area:** backend · **Depends on:** T1 · **Ralph:** **yes**
- **Why:** The core insight — which champs the player is actually good on right
  now. Involves paging match history, aggregating per champion, handling many
  edge cases and keeping within rate limits. Big and fiddly → Ralph.
- **Acceptance criteria**
  - [x] Fetch the last N matches for a PUUID (paged, cached per match).
  - [x] Aggregate games, wins, win-rate, avg KDA and CS/min per champion.
  - [x] Return the player's top champions by a sensible "form" score.
  - [ ] Handle players with few/no ranked games without erroring.
  - [ ] Stay within Riot rate limits (batched + cached).
  - [ ] Unit tests over a fixture match set assert the aggregation maths.

### T4 — AI draft assistant UI
- **Priority:** p2 · **Area:** frontend · **Depends on:** T1 · **Ralph:** no
- **Why:** The flagship AI feature; the backend endpoint already exists.
- **Acceptance criteria**
  - [x] Draft board: pick role, add allied picks, add enemy bans (champion pickers).
  - [x] Calls `POST /api/draft` and renders ranked suggestions with reasons.
  - [x] Loading and error states handled.
  - [x] Playwright test covers a suggestion render (mocked API).

### T5 — AI patch digest
- **Priority:** p2 · **Area:** backend · **Depends on:** T3 · **Ralph:** no
- **Why:** "What changed for the champs I play" — uses web search + Claude.
- **Acceptance criteria**
  - [ ] `GET /api/patch-digest?champions=...` returns a summarised digest.
  - [ ] Digest is scoped to the passed champions.
  - [ ] Result cached for the current patch.
  - [ ] Unit test with a stubbed AI client asserts the response shape.

### T6 — Redis cache backend
- **Priority:** p3 · **Area:** infra · **Depends on:** — · **Ralph:** no
- **Why:** In-memory cache doesn't survive restarts or scale past one worker.
- **Acceptance criteria**
  - [ ] Cache uses Redis when `REDIS_URL` is set, else in-memory.
  - [ ] Same interface — no route changes needed.
  - [ ] Tests cover both backends.

### T7 — Production deploy (DigitalOcean) + CI deploy step
- **Priority:** p2 · **Area:** infra · **Depends on:** T2, T4 · **Ralph:** no
- **Why:** A live link is the single biggest portfolio win.
- **Acceptance criteria**
  - [ ] App runs on a DO droplet via Docker Compose behind Nginx (TLS).
  - [ ] CI deploys on merge to `main` using GitHub Actions secrets.
  - [ ] Live URL and CI badge added to the README.
