# Deploying PoroPilot

This directory holds the production stack: `docker-compose.prod.yml` (Nginx + FastAPI
backend + Redis), `web.Dockerfile` (builds the Vue app and serves it via Nginx with a
reverse proxy to the backend), and `nginx.conf` (TLS + SPA + `/api` proxy).

The engineering is done; the steps below are the account-specific bits only you can do
(they need your DigitalOcean account, a domain and secrets).

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
cp backend/.env.example backend/.env    # then edit: add RIOT_API_KEY + ANTHROPIC_API_KEY
```

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

## 7. Finish the T7 acceptance criteria

Once it's live: add the **live URL** to the top-level `README.md` (there's a commented
placeholder next to the CI badge), then tick T7 in `tasks.md` and close the issue.

## Notes

- Swap the in-memory cache for Redis in production by setting `REDIS_URL` — the compose
  file already does this (`redis://redis:6379/0`), and see T6 for making the app use it.
