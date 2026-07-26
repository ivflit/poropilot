"""Thin async Riot API client with light caching.

Only the endpoints PoroPilot needs, wired for the platform/regional split.
The client wraps a shared httpx.AsyncClient (injected via dependency, created in
the app lifespan) so connections are pooled. Match details are cached long
(a finished game never changes); lookups short.
"""

import httpx

from app.cache import cache
from app.config import settings
from app.riot.regions import platform_host, regional_route
from app.schemas import MasteryEntry, Profile


class RiotAPIError(RuntimeError):
    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(f"Riot API {status_code}: {message}")
        self.status_code = status_code


class RiotClient:
    def __init__(self, http: httpx.AsyncClient, api_key: str | None = None) -> None:
        self._http = http
        self._key = api_key or settings.riot_api_key

    async def _get(self, host: str, path: str, ttl: int, cache_key: str):
        cached = await cache.get(cache_key)
        if cached is not None:
            return cached
        url = f"https://{host}.api.riotgames.com{path}"
        resp = await self._http.get(url, headers={"X-Riot-Token": self._key})
        if resp.status_code != 200:
            raise RiotAPIError(resp.status_code, resp.text)
        data = resp.json()
        await cache.set(cache_key, data, ttl=ttl)
        return data

    # --- Account-V1 (regional) ---
    async def account_by_riot_id(self, region_cluster: str, name: str, tag: str):
        return await self._get(
            region_cluster,
            f"/riot/account/v1/accounts/by-riot-id/{name}/{tag}",
            ttl=3600,
            cache_key=f"acct:{region_cluster}:{name}#{tag}",
        )

    # --- Summoner-V4 (platform) ---
    async def summoner_by_puuid(self, platform: str, puuid: str):
        return await self._get(
            platform,
            f"/lol/summoner/v4/summoners/by-puuid/{puuid}",
            ttl=600,
            cache_key=f"summ:{platform}:{puuid}",
        )

    # --- League-V4 (platform) — by PUUID; Summoner-V4 no longer returns an `id` ---
    async def league_entries(self, platform: str, puuid: str):
        return await self._get(
            platform,
            f"/lol/league/v4/entries/by-puuid/{puuid}",
            ttl=300,
            cache_key=f"league:{platform}:{puuid}",
        )

    # --- Champion-Mastery-V4 (platform) ---
    async def champion_masteries(self, platform: str, puuid: str, top: int = 10):
        return await self._get(
            platform,
            f"/lol/champion-mastery/v4/champion-masteries/by-puuid/{puuid}/top?count={top}",
            ttl=600,
            cache_key=f"mastery:{platform}:{puuid}:{top}",
        )

    # --- Match-V5 (regional) ---
    async def match_ids(
        self,
        region_cluster: str,
        puuid: str,
        start: int = 0,
        count: int = 20,
        queue: int | None = None,
    ):
        # Riot caps a single /ids request at 100; callers page via `start`.
        count = min(count, 100)
        path = f"/lol/match/v5/matches/by-puuid/{puuid}/ids?start={start}&count={count}"
        # The queue is part of the cache key as well as the query — otherwise a
        # solo-only page would be served from an unfiltered request's cache entry.
        key = f"matchids:{region_cluster}:{puuid}:{start}:{count}"
        if queue is not None:
            path += f"&queue={queue}"
            key += f":q{queue}"
        return await self._get(region_cluster, path, ttl=120, cache_key=key)

    async def match(self, region_cluster: str, match_id: str):
        return await self._get(
            region_cluster,
            f"/lol/match/v5/matches/{match_id}",
            ttl=86400,  # a finished match is immutable
            cache_key=f"match:{match_id}",
        )


async def load_profile(client: RiotClient, region_code: str, name: str, tag: str) -> Profile:
    """Aggregate a full profile from a region code + Riot ID."""
    platform = platform_host(region_code)
    cluster = regional_route(platform)

    account = await client.account_by_riot_id(cluster, name, tag)
    puuid = account["puuid"]
    summoner = await client.summoner_by_puuid(platform, puuid)
    entries = await client.league_entries(platform, puuid)
    masteries = await client.champion_masteries(platform, puuid)

    return Profile(
        riot_id=f"{account['gameName']}#{account['tagLine']}",
        region=region_code.upper(),
        level=summoner.get("summonerLevel"),
        profile_icon_id=summoner.get("profileIconId"),
        ranked=entries,
        top_masteries=[
            MasteryEntry(champion_id=m["championId"], points=m["championPoints"], level=m["championLevel"])
            for m in masteries
        ],
    )
