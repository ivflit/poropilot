"""FastAPI dependency providers.

The Riot client wraps the process-wide httpx.AsyncClient created in the app
lifespan, so connections are pooled across requests rather than opened per call.
"""

from fastapi import Request

from .champions import ChampionService
from .riot.client import RiotClient
from .schemas import Champion


def get_riot_client(request: Request) -> RiotClient:
    return RiotClient(request.app.state.http)


async def get_champion_map(request: Request) -> dict[int, Champion]:
    """Return the cached champion map, loading it once if startup didn't."""
    state = request.app.state
    if not getattr(state, "champions", None):
        service = ChampionService(state.http)
        state.ddragon_version, state.champions = await service.load()
    return state.champions
