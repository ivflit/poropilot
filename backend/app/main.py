"""PoroPilot API entrypoint — app wiring only; routes live in app/api/routes.py."""

import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.champions import ChampionService
from app.config import settings
from app.db import engine

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # One pooled HTTP client for the app's lifetime (shared by every request).
    app.state.http = httpx.AsyncClient(timeout=10)
    app.state.ddragon_version = None
    app.state.champions = {}

    # Warm the champion static data on startup. If Data Dragon is unreachable we
    # carry on — the /api/champions dependency will lazy-load on first request.
    try:
        service = ChampionService(app.state.http)
        app.state.ddragon_version, app.state.champions = await service.load()
    except Exception:
        logger.warning("Could not load champion data on startup; will lazy-load.")

    yield
    await app.state.http.aclose()
    if engine:
        await engine.dispose()


app = FastAPI(title="PoroPilot API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=settings.cors_origin_regex,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

app.include_router(router)

# Auth and user-data routes are only available when a database is configured.
if settings.database_url:
    from app.api.auth_routes import router as auth_router
    from app.api.pool_routes import router as pool_router

    app.include_router(auth_router)
    app.include_router(pool_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
