"""FastAPI dependency providers.

The Riot client wraps the process-wide httpx.AsyncClient created in the app
lifespan, so connections are pooled across requests rather than opened per call.
"""

from fastapi import Request

from .riot.client import RiotClient


def get_riot_client(request: Request) -> RiotClient:
    return RiotClient(request.app.state.http)
