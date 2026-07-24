"""FastAPI dependency providers.

The Riot client wraps the process-wide httpx.AsyncClient created in the app
lifespan, so connections are pooled across requests rather than opened per call.
"""

from fastapi import HTTPException, Request

from app.champions import ChampionService
from app.config import settings
from app.riot.client import RiotClient
from app.schemas import Champion


def ai_enabled() -> bool:
    return bool(settings.anthropic_api_key)


def require_ai() -> None:
    """Guard for AI endpoints — 503 when no Anthropic key is configured."""
    if not ai_enabled():
        raise HTTPException(
            status_code=503,
            detail="AI features are disabled: no ANTHROPIC_API_KEY configured.",
        )


def get_riot_client(request: Request) -> RiotClient:
    return RiotClient(request.app.state.http)


async def get_champion_map(request: Request) -> dict[int, Champion]:
    """Return the cached champion map, loading it once if startup didn't."""
    state = request.app.state
    if not getattr(state, "champions", None):
        service = ChampionService(state.http)
        state.ddragon_version, state.champions = await service.load()
    return state.champions


async def get_ddragon_version(request: Request) -> str:
    """The current Data Dragon (patch) version, loading champion data if needed."""
    state = request.app.state
    if not getattr(state, "ddragon_version", None):
        await get_champion_map(request)
    return state.ddragon_version
