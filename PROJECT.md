# LoL Companion — Build Plan

A League of Legends companion web app. Enter your **region + Riot ID (name#tag)**, and it loads your
profile, ranked stats, and champion pool; highlights your strongest champs in the current meta;
summarises the latest patch notes for the champs you play; and includes an AI **draft assistant** that
recommends a pick based on your role, your teammates' picks, and the enemy bans.

**Why this is a strong portfolio piece:** full-stack (Vue + Python), real external API integration,
meaningful AI use, automated testing, and full CI/CD — every skill on the CV, demonstrably.

---

## 1. Data sources (and the honest caveats)

| Need | Source | Notes |
|---|---|---|
| Name#tag → PUUID | Riot **Account-V1** (`/riot/account/v1/accounts/by-riot-id/{name}/{tag}`) | Regional routing (americas / asia / europe) |
| Profile (level, icon) | Riot **Summoner-V4** (`/lol/summoner/v4/summoners/by-puuid/{puuid}`) | Platform routing (euw1, na1, …) |
| Ranked tier / LP / W-L | Riot **League-V4** (`/lol/league/v4/entries/by-summoner/{id}`) | |
| Champion pool | Riot **Champion-Mastery-V4** (`.../champion-masteries/by-puuid/{puuid}`) | Mastery points ⇒ "your pool" |
| Match history + per-game stats | Riot **Match-V5** (`/lol/match/v5/matches/by-puuid/{puuid}/ids` → `.../matches/{id}`) | Regional routing; win-rate/role per champ |
| Champion/item static data + images + current patch version | **Data Dragon** (`ddragon.leagueoflegends.com`) | No API key, freely cacheable |

**Region handling:** user picks a platform (EUW, NA, …); you map platform → regional route for the
Account/Match calls. Keep a small lookup table.

**Rate limits:** a personal dev key is ~20 req/s, 100 req/2min. This is *why caching matters* — cache
PUUID lookups, match details (immutable once played), and Data Dragon aggressively. (Nice CV tie-in:
same debouncing/caching story as your work.)

**The two hard-data problems — be honest in the README:**
- **Patch notes** aren't in the Riot API. Best approach: an **AI pipeline** — `web_search` for the current
  patch notes, then Claude summarises "what changed for the champs you play." Clean, and it *is* the AI feature.
- **"Current meta" strength** has no official source. Don't scrape tier-list sites (ToS risk). Instead
  **derive it from the player's own data** (mastery + recent win-rate per champ), and use Claude +
  web-search for qualitative "is this champ strong on the current patch" context. State this clearly.

---

## 2. Architecture

```
Vue 3 (Vite, Pinia, Vue Router)  ──HTTP──▶  FastAPI (async)
        │                                        │
   search component                       ┌──────┼───────────────┐
   (debounce + cache)                      │      │               │
                                    Riot API    Redis cache   Claude API
                                    Data Dragon  (+ Postgres)  (coach / draft / patch)
```

- **Frontend:** Vue 3 + Vite, Pinia for state, Vue Router. (Optional: Tailwind for speed.)
- **Backend:** **FastAPI** — async fits the many concurrent Riot calls and streaming AI responses well,
  and shows breadth next to your Django day-job. (Django is fine too if you'd rather stay in one stack.)
- **Cache:** Redis (or SQLite/in-memory for the MVP). Cache Riot responses + Data Dragon.
- **DB (optional for MVP):** PostgreSQL — store looked-up profiles / cached match summaries.
- **AI:** Anthropic Claude API (see §4).

---

## 3. Features → build order

**Feature A — Profile lookup.** Region + name#tag → PUUID → profile, rank, mastery. Render a profile card.
**Feature B — Champion pool + strengths.** Combine mastery + recent match win-rates → ranked list of your
best champs, tagged with a meta note (from the AI/web-search context).
**Feature C — Patch digest.** AI-summarised latest patch notes, filtered to champs in your pool.
**Feature D — Draft assistant.** Inputs: your role, allied picks, enemy bans (and optionally enemy picks).
Output: ranked champion suggestions from your pool with one-line reasons. AI-powered (§4).

---

## 4. The AI pipeline (Claude API)

Use the official **Anthropic Python SDK** (`pip install anthropic`). Set `ANTHROPIC_API_KEY` in env.

**Model choice (your call — it's your bill):**
- **Claude Haiku 4.5** (`claude-haiku-4-5`) — $1 / $5 per 1M tokens. Cheapest; great for patch summaries and quick draft advice.
- **Claude Sonnet 5** (`claude-sonnet-5`) — $3 / $15. Better draft reasoning; good default.
- **Claude Opus 4.8** (`claude-opus-4-8`) — $5 / $25. Most capable; overkill for a hobby app but the strongest reasoning.

Start on **Haiku 4.5 or Sonnet 5** to keep costs sane; you can bump the model string later.

**Three AI features:**

1. **Patch digest** — `web_search` server tool → Claude summarises what changed for the user's champ list.
   ```python
   resp = client.messages.create(
       model="claude-haiku-4-5", max_tokens=1500,
       tools=[{"type": "web_search_20260209", "name": "web_search"}],
       messages=[{"role": "user", "content": f"Summarise the latest LoL patch changes for these champions: {champs}. Bullet points, note buffs/nerfs."}],
   )
   ```

2. **Draft assistant** — use **structured outputs** so the frontend gets clean JSON:
   ```python
   resp = client.messages.create(
       model="claude-sonnet-5", max_tokens=1024,
       output_config={"format": {"type": "json_schema", "schema": {
           "type": "object",
           "properties": {
               "suggestions": {"type": "array", "items": {
                   "type": "object",
                   "properties": {
                       "champion": {"type": "string"},
                       "reason": {"type": "string"},
                       "confidence": {"type": "string", "enum": ["low", "medium", "high"]}
                   },
                   "required": ["champion", "reason", "confidence"],
                   "additionalProperties": False
               }}
           },
           "required": ["suggestions"], "additionalProperties": False
       }}},
       messages=[{"role": "user", "content": draft_context}],  # role, your pool, ally picks, enemy bans
   )
   ```

3. **Coach note (optional stretch)** — feed recent match stats → a short "what to work on" summary.
   Use **streaming** (`client.messages.stream(...)`) so it renders live in the UI.

**Cost/perf tips:** put the big static context (champion list, your system prompt) first and add
`cache_control={"type": "ephemeral"}` for **prompt caching** (~90% cheaper on repeats). Always parse tool
inputs / structured output as JSON — never string-match.

---

## 5. CI/CD (GitHub Actions — mirror your Aevus setup)

`.github/workflows/ci.yml`: on every push/PR →
1. **Lint** — `ruff` (Python) + `eslint` (Vue).
2. **Test** — `unittest`/`pytest` for the backend, **Playwright** for the frontend E2E.
3. **Build** — Docker image(s).
4. **Deploy** (on merge to `main`) — push image to a registry, SSH to the DigitalOcean droplet, pull & restart.

Add the green **CI badge** to the README — it visibly proves the pipeline. Dockerise for local dev too
(a `docker-compose.yml` with api + frontend + redis + postgres) so `docker compose up` just works.

---

## 6. Suggested repo layout

```
lol-companion/
├── frontend/            # Vue 3 + Vite
│   ├── src/components/SummonerSearch.vue   # debounce + cache
│   └── tests/e2e/                          # Playwright
├── backend/             # FastAPI
│   ├── app/riot/        # Riot API client + region routing + caching
│   ├── app/ai/          # Claude pipelines (patch, draft, coach)
│   ├── app/api/         # routes
│   └── tests/           # unittest
├── docker-compose.yml
├── .github/workflows/ci.yml
└── README.md            # live demo link + screenshots + CI badge
```

---

## 7. Phased plan

- **MVP (weekend):** profile lookup (Features A) end-to-end, deployed, README with a live link. Riot key + caching.
- **v1:** champion pool/strengths (B) + the draft assistant (D, the flashy AI bit). Tests + CI green.
- **Stretch:** patch digest (C), coach note, ranked-progress charts, login to save your profile.

---

## 8. What makes it *count* (do these, not just the code)

- ✅ **Deployed** with a live link — put it at the top of the README and on your CV/GitHub.
- ✅ **README with screenshots** — the single biggest differentiator; most devs skip it.
- ✅ **Green CI badge** + tests that actually run in CI.
- ✅ **AI used meaningfully** (draft advice, patch digest) — not a bolted-on chatbot.
- ✅ Respect Riot's API ToS; never commit your API key (use env vars / GitHub secrets).
