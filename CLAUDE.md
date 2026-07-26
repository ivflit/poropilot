# CLAUDE.md — working guide for PoroPilot

Guidance for any agent (or human) working in this repo. Read this, then
`CONTEXT.md` (what/why) and `docs/ARCHITECTURE.md` (how it's built and run).

## What this project is

PoroPilot is a League of Legends companion web app: look up a summoner by region
and Riot ID, see their profile, champion pool and win-rates, get an AI draft
assistant and a patch digest. It's a portfolio project — code quality matters as
much as features.

## Before you write code

- **Load the right skill first.** Run the `fastapi-python` skill before touching
  backend code, and `vue3-frontend` before touching frontend code. We want
  industry-standard code, not first-draft code.
- Skim `tasks.md` and work only on the task you've picked.

## How we work (the loop)

1. **Tasks** live in `tasks.md` — each has a description, why it matters,
   acceptance criteria, priority, dependencies and a Ralph flag.
2. **Acceptance criteria** are checkboxes. A task is done only when every box is
   ticked *and backed by a passing test*.
3. **Issues** — a task becomes a GitHub issue (see `docs/issues/` for the
   template) with labels for priority (`p1`/`p2`/`p3`), area (`backend`/
   `frontend`/`infra`) and, where relevant, `ralph`. Note what blocks it.
4. **Order** — always take the first unblocked, highest-priority task. Don't
   start something whose dependencies aren't done.
5. **Tick off** — when a criterion is met and the tests prove it, change `[ ]`
   to `[x]` in `tasks.md` in the same commit as the work.

## Ralph — only for the big, complex tasks

Most tasks are small enough to do in one go — **do those normally.** The Ralph
loop (`ralph.sh`) is reserved for large, multi-step tasks with lots of moving
parts. A task opts in by setting **`Ralph: yes`** in `tasks.md` and carrying the
**`ralph`** label on its issue. If a task isn't flagged, don't loop it.

```bash
./ralph.sh T3        # iterate on task T3 until its acceptance criteria are met
./ralph.sh T3 20     # cap at 20 iterations (default 15)
```

The loop reads the task, implements the next unchecked criterion, runs the tests,
ticks the box only if they pass, and commits — repeating until done.

## Git workflow

- **Issue first.** Every change starts as a GitHub issue — it gets a number.
- **Branch `feature/<issue-number>-<short-name>`** (e.g. `feature/17-project-docs`). The
  issue number is required in the branch name.
- **Open a PR; merge to `main` only once CI passes.** `main` is branch-protected — the
  `backend` and `frontend` checks must be green. Squash-merge and delete the branch.
- Never commit directly to `main`.
- After merging a frontend change, refresh the running app:
  `docker compose up -d --build --force-recreate frontend`.

## Conventions

**Commits** — short, present-tense, plain UK English, as a person would write
them ("Add champion lookup service", not "feat: implement ChampionService").
No AI/Claude/co-author attribution in commit messages, ever.

**Backend (FastAPI)** — Pydantic models for every request/response (RORO),
dependency injection, one pooled `httpx.AsyncClient` via the app lifespan, thin
routers in `app/api/`, `async def` for I/O. Guard clauses and early returns.

**Frontend (Vue 3)** — `<script setup>`, reusable logic in `composables/`, the
API layer in `services/`, small focused components.

## Commands

```bash
# Backend
cd backend && python -m unittest discover        # tests
cd backend && ruff check .                        # lint
uvicorn app.main:app --reload                     # run

# Frontend
cd frontend && npx playwright test                # e2e tests
cd frontend && npm run dev                         # run

# Everything
docker compose up --build
```

## Guardrails

- Never commit secrets. Real keys live in `backend/.env` (gitignored).
- Respect the Riot API terms and its rate limits — cache aggressively.
