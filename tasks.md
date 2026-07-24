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
  - [x] Handle players with few/no ranked games without erroring.
  - [x] Stay within Riot rate limits (batched + cached).
  - [x] Unit tests over a fixture match set assert the aggregation maths.

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
  - [x] `GET /api/patch-digest?champions=...` returns a summarised digest.
  - [x] Digest is scoped to the passed champions.
  - [x] Result cached for the current patch.
  - [x] Unit test with a stubbed AI client asserts the response shape.

### T6 — Redis cache backend
- **Priority:** p3 · **Area:** infra · **Depends on:** — · **Ralph:** no
- **Why:** In-memory cache doesn't survive restarts or scale past one worker.
- **Acceptance criteria**
  - [x] Cache uses Redis when `REDIS_URL` is set, else in-memory.
  - [x] Same interface — no route changes needed.
  - [x] Tests cover both backends.

### T7 — Production deploy (DigitalOcean) + CI deploy step
- **Priority:** p2 · **Area:** infra · **Depends on:** T2, T4 · **Ralph:** no
- **Why:** A live link is the single biggest portfolio win.
- **Acceptance criteria**
  - [ ] App runs on a DO droplet via Docker Compose behind Nginx (TLS).
  - [ ] CI deploys on merge to `main` using GitHub Actions secrets.
  - [ ] Live URL and CI badge added to the README.

### T8 — Expose champion pool via API and show it in the profile
- **Priority:** p2 · **Area:** backend + frontend · **Depends on:** T3 (done) · **Ralph:** no
- **Why:** T3 built and tested the champion-pool analysis, but it isn't wired to
  an endpoint or shown anywhere. Expose it and surface it in the UI.
- **Acceptance criteria**
  - [x] `GET /api/pool/{region}/{name}/{tag}` returns the champion pool (top + per-champ stats).
  - [x] Result reuses cached match data (no extra Riot calls on repeat).
  - [x] Profile view shows the top champions with win-rate and form.
  - [x] Backend route test (stubbed client) and a Playwright test for the UI.

### T9 — SCSS styling system (remove inline component styles)
- **Priority:** p3 · **Area:** frontend · **Depends on:** — · **Ralph:** no
- **Why:** Styles are scattered across component `<style>` blocks. Centralise
  them in an SCSS system with shared design tokens; components carry markup and
  logic only.
- **Acceptance criteria**
  - [x] SCSS build set up (`sass`), with a `src/styles/` architecture and design tokens.
  - [x] No `<style>` blocks remain in any `.vue` component.
  - [x] App still renders correctly (all Playwright tests pass).

### T10 — Gracefully disable AI features when no Anthropic key
- **Priority:** p2 · **Area:** backend + frontend · **Depends on:** — · **Ralph:** no
- **Why:** An Anthropic key is paid; the app must run fully without it, with the
  AI features (draft assistant, patch digest) cleanly switched off rather than
  erroring or crashing on startup.
- **Acceptance criteria**
  - [x] App starts without an Anthropic key (no import-time client construction).
  - [x] `GET /api/config` reports whether AI is enabled.
  - [x] `/api/draft` and `/api/patch-digest` return 503 when no key is set.
  - [x] Frontend hides the draft board when AI is disabled.
  - [x] Tests cover the disabled backend path and the hidden UI.

### T11 — Gemini AI backend (free-tier provider option)
- **Priority:** p2 · **Area:** backend · **Depends on:** T10 · **Ralph:** no
- **Why:** An Anthropic key is paid and blocked on the work org; Gemini has a free
  tier and works when deployed. Add it as a selectable provider so the AI features
  can run at zero cost, without dropping the Anthropic path.
- **Acceptance criteria**
  - [x] `AI_PROVIDER` selects the backend (`anthropic` | `gemini`); unset auto-detects from whichever key is set, else AI stays off.
  - [x] Gemini backend implements the draft assistant and patch digest with structured JSON output.
  - [x] `GET /api/config` and the 503 guard recognise the Gemini key too.
  - [x] Tests cover the Gemini backend (stubbed client) and provider selection.

### T12 — Draft assistant: enemy picks + out-of-pool suggestions
- **Priority:** p2 · **Area:** backend + frontend · **Depends on:** T4 · **Ralph:** no
- **Why:** The assistant should factor in the enemy team's picks, and still give
  useful advice when the player's pool is empty or a poor fit — by also suggesting
  strong picks for the role outside their pool, clearly flagged.
- **Acceptance criteria**
  - [x] Draft board collects enemy picks (alongside bans) and sends them to the API.
  - [x] Suggestions include strong role picks outside the pool when the pool is weak/empty, each flagged in/out of pool.
  - [x] UI shows whether each suggestion is from the player's pool or a meta pick.
  - [x] Tests updated (schema + frontend).
