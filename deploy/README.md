# Deploying PoroPilot

Two supported paths. **Option A is free** and needs no server, domain or TLS work —
start there. Option B is the "own the box" setup, worth doing for the DevOps story.

| | A · Netlify + Render | B · DigitalOcean droplet |
|---|---|---|
| Cost | £0 | ~£5/mo + domain |
| Setup | Two Git connections | Droplet, DNS, certbot, SSH secrets |
| TLS | Automatic | certbot, renewed by you |
| Caveat | Backend sleeps when idle (~30–60s cold start) | You operate it |
| Config | `render.yaml`, `netlify.toml` | `deploy/*` |

Everything in the repo is done; the steps below are the account-specific bits only you
can do.

---

# Option A · Free deploy (Netlify + Render)

The frontend is a static bundle and the backend is a container, so they can be hosted
separately on two free tiers. Because they end up on different domains the browser call
is **cross-origin** — hence the `CORS_ORIGINS` step, which is the one thing that catches
people out.

## A1. Backend on Render

1. Render → **New → Blueprint** → connect this repo. Render reads `render.yaml` and
   creates the `poropilot-api` web service plus a free `poropilot-cache` Key Value
   store (Redis-compatible, already wired to `REDIS_URL`).
2. Set the secrets it asked you to fill in (Environment tab):
   - `RIOT_API_KEY` — **required**. Use a *personal* key (developer.riotgames.com →
     Register Product); the plain dev key expires every 24h.
   - `GEMINI_API_KEY` — optional, free tier at https://aistudio.google.com. Leave the
     AI keys blank and the draft assistant + patch digest simply switch off.
   - `CORS_ORIGINS` — leave blank for now; you need the Netlify URL first.
3. Note the service URL, e.g. `https://poropilot-api.onrender.com`. Check
   `…/health` returns `{"status":"ok"}`.

## A2. Frontend on Netlify

1. Netlify → **Add new site → Import an existing project** → pick this repo. It reads
   `netlify.toml`, so the build settings and the SPA redirect are already right.
2. Site configuration → **Environment variables** → add
   `VITE_API_BASE = https://poropilot-api.onrender.com` (your Render URL, no trailing
   slash). This is inlined at build time, so it needs a redeploy to take effect — and
   it must never hold a secret.
3. Deploy. Note the site URL, e.g. `https://poropilot.netlify.app`.

## A3. Close the loop on CORS

Back in Render, set on the backend service:

- `CORS_ORIGINS=https://poropilot.netlify.app` — comma-separated if you have more than
  one (a custom domain, say). **No trailing slashes.**
- `CORS_ORIGIN_REGEX=https://.*--poropilot\.netlify\.app` — optional, lets Netlify
  deploy previews and branch builds reach the API too.

Redeploy the backend. Both hosts auto-deploy on every push to `main` from here on.

> **If the app says "Failed to fetch":** check the backend logs before assuming CORS.
> An unhandled 500 carries no CORS header, so a real server error looks identical to a
> CORS failure in the browser.

## A4. Finish up

Add the live URL to the top-level `README.md` (there's a placeholder by the CI badge).

---

# Option B · DigitalOcean droplet

This directory holds the production stack: `docker-compose.prod.yml` (Nginx + FastAPI
backend + Redis), `web.Dockerfile` (builds the Vue app and serves it via Nginx with a
reverse proxy to the backend), and `nginx.conf` (TLS + SPA + `/api` proxy).

Here the frontend is served from the same origin as the API (Nginx proxies `/api`), so
`VITE_API_BASE` is empty and no `CORS_ORIGINS` setting is needed.

## 1. Provision the droplet

- Create a small DigitalOcean droplet (Ubuntu LTS, 1–2 GB RAM is plenty).
- Point a DNS **A record** for your domain (e.g. `poropilot.yourdomain.com`) at the
  droplet's IP.
- SSH in and install Docker + the compose plugin:
  ```bash
  curl -fsSL https://get.docker.com | sh
  ```

## 2. Get the code and secrets onto the server

```bash
git clone https://github.com/ivflit/poropilot.git
cd poropilot
cp backend/.env.example backend/.env    # then edit the keys (see below)
```

**Keys to set in `backend/.env`:**
- `RIOT_API_KEY` — **required** (profile, champ pool, win-rates). A *personal* Riot
  key (from developer.riotgames.com → Register Product) doesn't expire, unlike the
  24h dev key — use that for a live site.
- **AI features are optional.** Leave the AI keys blank and the draft assistant +
  patch digest simply switch off. To enable them live, pick one:
  - **Gemini (free):** set `GEMINI_API_KEY` from https://aistudio.google.com. This is
    the recommended option for a deployed site — free tier, hosted, no billing.
    `AI_PROVIDER` auto-detects it.
  - **Anthropic (paid):** set `ANTHROPIC_API_KEY` from console.anthropic.com instead.

## 3. Set your domain

Edit `deploy/nginx.conf` and replace **poropilot.example.com** (3 places) with your
real domain.

## 4. Obtain TLS certificates (once)

Nginx won't start without certs. Get them with certbot on the host:

```bash
sudo apt-get install -y certbot
sudo certbot certonly --standalone -d poropilot.yourdomain.com
```

Certs land in `/etc/letsencrypt/…`, which the `web` container mounts read-only.
(Set up a renewal cron/systemd timer for `certbot renew`.)

## 5. First deploy

```bash
docker compose -f deploy/docker-compose.prod.yml up -d --build
```

Visit `https://poropilot.yourdomain.com` — the SPA loads and `/api/...` is proxied
to the backend. Backend API docs are intentionally not exposed publicly by Nginx.

## 6. Automatic deploys from CI

The `.github/workflows/deploy.yml` workflow SSHes in and re-runs the compose command
on every push to `main`. Turn it on:

1. Add an SSH key the droplet trusts, and in the repo **Settings → Secrets and
   variables → Actions**:
   - **Secrets:** `DEPLOY_HOST` (droplet IP), `DEPLOY_USER`, `DEPLOY_SSH_KEY`
     (the private key), `DEPLOY_PATH` (e.g. `/root/poropilot`).
   - **Variable:** `DEPLOY_ENABLED` = `true`.
2. Push to `main` — the deploy job runs. Until `DEPLOY_ENABLED` is `true`, the job
   is skipped, so it never fails the build.

## 7. Finish up

Once it's live: add the **live URL** to the top-level `README.md` (there's a commented
placeholder next to the CI badge), then tick T7 in `tasks.md` and close the issue.

## Notes

- Swap the in-memory cache for Redis in production by setting `REDIS_URL` — the compose
  file already does this (`redis://redis:6379/0`), and see T6 for making the app use it.
