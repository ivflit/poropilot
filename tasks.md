# Tasks — PoroPilot backlog

Each task has a priority (p1 highest), dependencies, a Ralph flag (only big,
complex tasks use the `ralph.sh` loop — see `CLAUDE.md`), and acceptance criteria.
Tick a box only when the work is done **and** a test proves it.

## Order of play

```
T1 (champion data)  ── blocks ──▶ T2, T3, T4
T3 (pool + winrate) ── blocks ──▶ T5
T2, T4              ── blocks ──▶ T7 (deploy), T16 (free deploy)
T6 (Redis)          independent

T17 (accounts)      ── blocks ──▶ T18 (saved pools), T20 (AI review)
T19 (match filter)  ── blocks ──▶ T20 (AI post-game review), T21 (filter layout), T22 (match history)
```

T1–T15, T17–T24 are done. T16 awaits deploy accounts.

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

### T13 — Searchable champion picker with icons
- **Priority:** p2 · **Area:** frontend · **Depends on:** T4 · **Ralph:** no
- **Why:** Selecting from a 170-item `<select>` is poor UX. Replace it with a
  search-as-you-type control that shows champion icons in the results (loldle-style).
- **Acceptance criteria**
  - [x] Typing filters champions; results show the champion icon + name.
  - [x] Selecting a result adds a removable chip (with icon); no giant dropdown.
  - [x] Used by all four draft pickers (pool, allies, bans, enemy picks).
  - [x] Playwright test updated to the search interaction.

### T14 — Apply the new visual design (light + dark themes)
- **Priority:** p2 · **Area:** frontend · **Depends on:** T13 · **Ralph:** no
- **Why:** Adopt the designed UI — a proper token system, Space Grotesk/Manrope
  fonts, card surfaces, and light + dark themes.
- **Acceptance criteria**
  - [x] Design tokens as CSS custom properties with light (`:root`) and dark (`[data-theme="dark"]`) themes.
  - [x] Space Grotesk (display/numbers) + Manrope (body) fonts loaded.
  - [x] Components restyled as cards to match the mock; all existing states preserved.
  - [x] A theme toggle that persists and defaults to the system preference.
  - [x] All Playwright tests still pass.

### T15 — Rebuild the UI layout to match the design mockup
- **Priority:** p2 · **Area:** frontend · **Depends on:** T14 · **Ralph:** no
- **Why:** T14 applied only the tokens (decoded from a bundled export); the actual
  two-column dashboard layout was missing. Decoded the bundle + used the screenshot
  to rebuild the real design.
- **Acceptance criteria**
  - [x] Two-column dashboard: search bar, profile/mastery/recent-form cards (left), draft assistant (right).
  - [x] Profile card with gradient banner, Data Dragon avatar, rank badge + win-rate.
  - [x] Draft assistant: segmented role control, 2×2 icon pickers, numbered suggestion cards with tags + signal bars.
  - [x] Matches the mock's fonts, radii and colours; light + dark preserved.
  - [x] All tests pass.

### T16 — Free deploy: env-driven CORS + Render/Netlify config (roadmap R1)
- **Priority:** p1 · **Area:** infra · **Depends on:** T2, T4 · **Ralph:** no
- **Why:** A live URL is the single biggest portfolio signal. T7's droplet stack needs a
  paid server, a domain and manual TLS; this adds a **zero-cost** path (Netlify frontend +
  Render backend) that auto-deploys on merge. Split hosting means cross-origin calls, so
  CORS has to be configurable — and `CORS_ORIGINS` as a `list[str]` only accepted JSON
  from the environment, which crashed the app on a plain URL.
- **Acceptance criteria**
  - [x] `CORS_ORIGINS` accepts a comma-separated list (and still JSON); whitespace and
        trailing slashes tolerated.
  - [x] `CORS_ORIGIN_REGEX` allows preview/branch deploys (Netlify gives each a fresh subdomain).
  - [x] `render.yaml` blueprint deploys the backend + a free Key Value (Redis) store.
  - [x] `netlify.toml` builds the frontend with the SPA redirect and asset caching.
  - [x] `frontend/.env.example` documents `VITE_API_BASE`; `backend/.env.example` documents CORS.
  - [x] `deploy/README.md` covers both the free path and the droplet path.
  - [x] Unit tests cover the origin parsing (comma, JSON, blank, trailing slash, regex).
  - [ ] Live URL added to the README. *(Needs Ivan's Netlify/Render accounts — see
        `deploy/README.md` Option A.)*

---

## The accounts arc (T17 → T20)

Everything below hangs off having a real user account. T17 introduces the first database
in the project, so do it first and do it properly.

### T17 — Accounts: sign up and log in
- **Priority:** p2 · **Area:** backend + frontend · **Depends on:** — · **Ralph:** **yes**
- **Why:** Nothing can be *saved* today — every visit starts from an empty search box.
  Accounts unlock saved champion pools (T18) and personalised analysis (T20), and they
  introduce a real database, password handling and auth flows. Big and fiddly, touching
  both ends of the stack → Ralph.
- **Design notes**
  - Postgres via SQLAlchemy 2.0 async + Alembic migrations. Free tiers: Render Postgres
    or Neon. Keep the cache (Redis) separate — the DB is for durable user data only.
  - Email + password with Argon2 hashing (`argon2-cffi`), short-lived JWT access token
    plus a refresh token in an httpOnly cookie. Don't hand-roll the crypto.
  - A user optionally links one Riot ID (region + name + tag) so the app can open on
    their own profile.
- **Acceptance criteria**
  - [x] Postgres + async SQLAlchemy + Alembic wired in; `DATABASE_URL` env-driven, and
        the app still starts (with auth routes disabled) when it's unset.
  - [x] `POST /api/auth/signup` and `POST /api/auth/login` return tokens; passwords are
        Argon2-hashed and never logged or returned.
  - [x] `POST /api/auth/logout`, `POST /api/auth/refresh`, and `GET /api/auth/me` for the
        current user.
  - [x] A `get_current_user` dependency protects authenticated routes; a bad/expired
        token gives 401, not 500.
  - [x] Users can link a Riot ID to their account; the app opens on it when logged in.
  - [x] Frontend: sign-up and log-in forms, a session composable, header shows the
        signed-in user with a log-out control; the whole app still works logged **out**.
  - [x] Tests: backend covers signup/login/refresh/401 paths and duplicate-email
        rejection (22 tests); Playwright covers the log-in journey (6 tests).
- **Open question (Ivan, 50/50 on this):** should an account also keep a **history of
  previous sessions** — the summoners you looked up, drafts you ran? Deferred until T17
  lands; it's a small additive table (`search_history`) if we want it. Not in scope here.

### T18 — Saved champion pools per role, loaded into the draft assistant
- **Priority:** p2 · **Area:** backend + frontend · **Depends on:** T17 · **Ralph:** no
- **Why:** You retype your pool into the draft board every single time. And most players
  are a two-role main (top *and* mid, say) with a different pool for each — one flat
  saved list wouldn't fit. Save a pool **per role**, then load it in one click.
- **Acceptance criteria**
  - [x] A user can save a champion pool for **each** role (TOP/JUNGLE/MID/ADC/SUPPORT)
        and hold several at once; saving a role again replaces that role's pool only.
  - [x] `GET/PUT/DELETE /api/me/pools` (and `/api/me/pools/{role}`) — authenticated,
        scoped to the caller, with the usual Pydantic in/out.
  - [x] Picking a role in the draft assistant auto-loads that role's saved pool; the user
        can still edit the loaded pool without overwriting what's saved.
  - [x] A one-click "save this as my {role} pool", and seeding a pool from the summoner's
        analysed champion pool (T8) rather than typing it out.
  - [x] Logged-out users keep today's behaviour (manual entry, nothing saved).
  - [x] Tests: route tests for the CRUD and cross-user isolation (user A cannot read or
        write user B's pools); Playwright covers save → reload → auto-load.

### T19 — Filter matches by queue (all / ranked solo-duo / ranked flex)
- **Priority:** p2 · **Area:** backend + frontend · **Depends on:** T3 · **Ralph:** no
- **Why:** Today every match is lumped together, so ARAM and normals pollute the win-rates
  and the champion pool — the numbers don't reflect how you actually perform in ranked.
  Solo-duo and flex are different games and deserve separate stats.
- **Design notes**
  - Riot queue IDs: **420** ranked solo/duo, **440** ranked flex, **400/430** normals,
    **450** ARAM. Match-V5's match-ids endpoint takes a `queue` parameter, so filter at
    the source where we can and by `info.queueId` on cached matches otherwise.
- **Acceptance criteria**
  - [x] `GET /api/pool/...` and the match endpoints accept a `queue` filter
        (`all` | `solo` | `flex`), validated by an enum — a bad value gives 422.
  - [x] Aggregate stats (games, win-rate, KDA, CS/min, form) recompute per filter.
  - [x] Cache keys include the filter, so switching filters doesn't serve stale numbers
        or trigger a re-fetch of matches we already hold.
  - [x] A segmented control in the UI switches the filter and updates profile, recent
        form and champion pool together.
  - [x] Empty state when the player has no games in the selected queue.
  - [x] Tests: fixture-based aggregation asserts each filter over a mixed match set;
        Playwright covers switching the filter.

### T20 — AI post-game review of recent ranked games
- **Priority:** p2 · **Area:** backend + frontend · **Depends on:** T19 · **Ralph:** no
- **Why:** Stats tell you *what* happened, not *what to do differently*. Turn a recent
  ranked game's numbers into plain coaching — "you were 2k gold down by 15 and died 4
  times pre-first-item, so you had no impact; farm safely to your two-item spike and
  look for a play then." This is the feature that makes the app feel like a coach.
- **Design notes**
  - Reuse the provider-agnostic AI layer (`ai/provider.py`) so it works on Anthropic
    *and* Gemini, with structured JSON out, and returns 503 when no key — same as the
    draft assistant.
  - Feed it **derived** stats, not the raw match blob: gold/XP/CS differential vs the
    lane opponent at 10 and 15, deaths and when they happened, damage share, vision,
    objective participation, KDA, game length. Ground the advice in numbers so it
    can't invent a narrative.
- **Acceptance criteria**
  - [x] `GET /api/review/{region}/{name}/{tag}/{match_id}` returns a structured
        review: a one-line verdict, 2–4 specific things that went wrong each citing the
        stat behind it, and 2–3 concrete things to do next game.
  - [x] Scoped to ranked games (uses T19's queue filter); rejects non-ranked with a
        clear message (422).
  - [x] Every point is grounded in a stat we actually computed — no advice without a
        number behind it.
  - [x] Cached per match + player (an AI call per page view would be wasteful and slow).
  - [x] Degrades cleanly with no AI key (503 + the UI hides the panel), exactly like the
        draft assistant.
  - [x] UI: pick a recent ranked game, see the review, with loading and error states.
  - [x] Tests: stat derivation tested against a fixture match (15 tests); Playwright
        covers the review UI (5 tests); the no-key path is covered.

### T21 — Make the queue filter's effect visible in the layout
- **Priority:** p2 · **Area:** frontend · **Depends on:** T19 · **Ralph:** no
- **Why:** T19 works, but you can't *see* it work. Switching the filter changes the
  recent-form card and the rank badge — and recent form sits at the bottom of the left
  column, below a profile card and a mastery card that (correctly) don't move. The
  result is a control that looks broken: you click it and nothing appears to happen.
- **Design notes**
  - **Champion mastery is lifetime data** — Riot doesn't scope mastery by queue, so it
    can never respond to the filter. Rather than hide it, label it honestly ("all time")
    so it's clear it isn't stale.
  - The fix is proximity and feedback: put the queue-dependent content next to the
    control that changes it. Options worth trying — move recent form to the top of the
    column; move the filter onto the recent-form card's header; or promote recent form
    into its own wider panel.
  - A brief transition or highlight when the numbers change would confirm the click
    registered, especially when a filter returns similar-looking values.
  - Bear in mind T20 will add a post-game review panel that's also queue-scoped, and
    T3/R3's match list will be too — so the layout should have an obvious home for
    "things that respond to the filter" rather than being tuned for one card.
- **Acceptance criteria**
  - [x] Switching the queue filter produces an obvious, immediate visible change without
        scrolling, at desktop and mobile widths.
  - [x] Queue-dependent content (recent form, rank badge) is visually grouped with, or
        adjacent to, the filter control.
  - [x] Champion mastery is labelled as all-time so it doesn't read as stale.
  - [x] Light and dark themes both hold up; existing card styling and tokens reused
        (no hard-coded colours).
  - [x] Playwright covers the reordered layout; all existing tests still pass.

---

## Match history arc

### T22 — Match history with filtering and sorting
- **Priority:** p2 · **Area:** backend + frontend · **Depends on:** T19 · **Ralph:** no
- **Why:** Every stat site (op.gg, porofessor, shok.lol) has a full match history as
  its core feature. PoroPilot shows champion pool stats and AI reviews but no way to
  browse individual matches.
- **Acceptance criteria**
  - [x] `GET /api/history/{region}/{name}/{tag}` returns rich match details: all 10
        participants, lane opponent, CS, CS/min, damage, DPM, gold, vision, role,
        game timestamp; supports `count` and `start` params for pagination.
  - [x] Filters: `role` (All/Top/Jungle/Middle/Bottom/Utility) and `result` (All/Win/Loss)
        query params validated by enums (bad value → 422); `sort` param (newest/oldest/
        cs_min/dmg_min).
  - [x] Frontend: match history panel with match rows, role filter tabs, W/L filter tabs,
        sort dropdown, "Load more" pagination.
  - [x] Each match row shows result bar (green/red), champion + role vs opponent, KDA,
        CS/min, damage, duration, time ago.
  - [x] Clicking a match row expands to show all 10 participants split by team (blue/red).
  - [x] Tests: 9 unit tests for `build_match_detail`, 12 route tests for filtering/sorting/
        pagination; 7 Playwright tests cover the UI.

### T23 — Aggregate stats card: overall W/L, win%, KDA ratio
- **Priority:** p2 · **Area:** backend + frontend · **Depends on:** T22 · **Ralph:** no
- **Why:** The profile shows rank and champion pool but no overall match stats. Every stat
  site shows total W/L, overall win%, and average KDA prominently.
- **Acceptance criteria**
  - [x] `/api/history/` response includes `aggregate` object: wins, losses, win_rate,
        avg_kills, avg_deaths, avg_assists, kda_ratio.
  - [x] Frontend: aggregate stats card with W/L record, win% SVG ring chart, avg KDA per
        game, KDA ratio. Deaths highlighted in error colour.
  - [x] Aggregate responds to role/result filters (computed over all filtered matches, not
        just the current page).
  - [x] Tests: 3 unit tests for `compute_aggregate`, 3 route tests for aggregate in the
        response; 1 Playwright test for the card.

### T24 — Enhanced champion performance: all champions with KDA
- **Priority:** p2 · **Area:** frontend · **Depends on:** T22 · **Ralph:** no
- **Why:** The recent form card only showed the top 5 champions. Stat sites show all
  played champions with games count and KDA for each.
- **Acceptance criteria**
  - [x] Recent form card shows all champions with a "Show all N" toggle (default top 5).
  - [x] Each row shows games count and KDA alongside the win-rate bar.
  - [x] Tests: 2 Playwright tests (win-rate + KDA display, show-all toggle).
