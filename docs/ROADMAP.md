# PoroPilot — Roadmap (make it CV-impressive)

Future work that would take PoroPilot from "solid portfolio app" to "genuinely
impressive," each tagged with the **skill it demonstrates** to an employer, a rough
size, and dependencies. Roughly ordered by impact-per-effort. Follow the usual flow
(issue → `feature/<n>-name` → PR → merge on green CI).

## Tier 1 — highest impact

### R1 · Ship it live (finish T7) + a real CI/CD pipeline
- **Shows:** DevOps, Docker, CI/CD, cloud. **Size:** M.
- A live URL is the single biggest signal on a CV. Deploy the frontend to a free static
  host and the backend to a free service (see below), wire auto-deploy on merge to `main`,
  add the live link + CI badge to the README. Bonus: a `staging` environment + GitHub
  Environments with required reviewers.

### R2 · Live game tracker (Spectator-V4)
- **Shows:** real-time data, API depth, product sense. **Size:** M.
- If the summoner is in a live game, show it, with both teams' champions — and let the
  draft assistant **auto-fill from the live game**. High wow-factor and unique.

### R3 · Match history detail
- **Shows:** data-rich UI, data modelling. **Size:** M.
- A list of recent matches with per-game KDA, items, CS, and a win/loss timeline. Turns
  the "recent form" numbers into a proper, clickable history.

## Tier 2 — strong depth signals

### R4 · Accounts + saved summoners/pools
- **Shows:** auth, persistence, security. **Size:** M–L.
- Sign in (OAuth or JWT), favourite summoners, save your champion pool so the draft
  assistant remembers it. Introduces a real DB (Postgres) and auth flows.

### R5 · Rate-limit resilience + performance
- **Shows:** backend rigour, systems thinking. **Size:** M.
- A proper Riot rate-limiter (token bucket honouring the response headers), Redis in prod,
  request coalescing, and a small load test (Locust/k6) with numbers in the README.

### R6 · Observability
- **Shows:** SRE/production-readiness. **Size:** S–M.
- Structured logging, Prometheus metrics + a Grafana dashboard (or Sentry for errors),
  and `/health` + `/ready` endpoints. "I can operate what I build."

### R7 · AI quality: streaming, caching, and evals
- **Shows:** AI engineering beyond a single call. **Size:** M.
- Stream draft suggestions token-by-token, cache AI results per draft state, and add an
  **eval harness** (LLM-as-judge over fixture drafts) so AI changes are measured, not vibes.

## Tier 3 — polish & breadth

### R8 · Real-time collaborative draft (WebSockets)
- **Shows:** concurrency, WebSockets. **Size:** L. Multiple people share a live draft board.

### R9 · Champion analytics & comparison
- **Shows:** data viz. **Size:** M. Trends over time, a synergy/counter matrix, charts.

### R10 · PWA + accessibility + Lighthouse CI
- **Shows:** frontend craft, a11y. **Size:** S–M. Installable/offline shell, a WCAG AA pass,
  and Lighthouse budgets enforced in CI.

### R11 · Test depth + coverage badge
- **Shows:** testing discipline. **Size:** S. Coverage reporting with a badge, contract
  tests for the Riot client, and a component-test layer for Vue.

### R12 · Infrastructure as code
- **Shows:** IaC/cloud maturity. **Size:** M. Terraform for the host + DNS + secrets, so the
  whole environment is reproducible from the repo.

---

**If you only do three:** R1 (live link) → R2 (live game tracker) → R6 (observability).
That trio reads as "ships to production, builds something genuinely useful in real time,
and runs it like a professional."
