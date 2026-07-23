# CONTEXT — PoroPilot

The background a newcomer (or agent) needs that isn't obvious from the code.

## What it is and who it's for

PoroPilot is a League of Legends companion web app. A player enters their
**region** and **Riot ID** (`name#tag`) and gets:

- their profile and ranked standing,
- their champion pool with win-rates and recent form,
- an **AI draft assistant** that suggests a pick from their pool given their
  role, allied picks and enemy bans,
- an **AI patch digest** summarising the latest patch for the champs they play.

It's a personal portfolio project — its job is to show full-stack, AI and DevOps
skills to prospective employers. Polish and correctness matter.

## Key decisions (and why)

- **FastAPI, not Django, for the backend.** The app is I/O-bound (lots of
  concurrent Riot calls) and async suits it; it also shows breadth alongside a
  Django day job.
- **We derive "champion strength" from the player's own data**, not a scraped
  tier list. Live meta strength has no official API and scraping third-party
  tier sites risks their terms — so strength comes from the player's mastery and
  recent win-rates, with the AI adding qualitative meta context.
- **Patch notes come via the AI pipeline** (web search + Claude), because they
  aren't in the Riot API.
- **Claude model is configurable** (`ANTHROPIC_MODEL`), defaulting to
  `claude-haiku-4-5` to keep a hobby project cheap. Bump to `claude-sonnet-5`
  for stronger draft reasoning.
- **Caching is a first-class concern**, not an afterthought — the Riot dev key is
  tightly rate-limited (~20 req/s), so responses are cached (finished matches
  forever, lookups briefly).

## External services

- **Riot Games API** — needs a free developer key from
  https://developer.riotgames.com. Endpoints used: Account-V1, Summoner-V4,
  League-V4, Champion-Mastery-V4, Match-V5.
- **Data Dragon** — Riot's static data CDN (champion/item data + images). No key.
- **Anthropic Claude API** — the AI features. Needs `ANTHROPIC_API_KEY`.

## Legal

PoroPilot isn't endorsed by Riot Games. Follow the Riot API terms of service.
