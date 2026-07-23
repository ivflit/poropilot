"""Thin async Riot API client with light caching.

Only the endpoints PoroPilot needs, wired for the platform/regional split.
The client wraps a shared httpx.AsyncClient (injected via dependency, created in
the app lifespan) so connections are pooled. Match details are cached long
(a finished game never changes); lookups short.
"""

import httpx

from ..cache import cache
from ..config import settings
from ..schemas import MasteryEntry, Profile
from .regions import platform_host, regional_route


class RiotAPIError(RuntimeError):
    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(f"Riot API {status_code}: {message}")
        self.status_code = status_code


class RiotClient:
    def __init__(self, http: httpx.AsyncClient, api_key: str | None = None) -> None:
        self._http = http
        self._key = api_key or settings.riot_api_key

    async def _get(self, host: str, path: str, ttl: int, cache_key: str):
        cached = cache.get(cache_key)
        if cached is not None:
            return cached
        url = f"https://{host}.api.riotgames.com{path}"
        resp = await self._http.get(url, headers={"X-Riot-Token": self._key})
        if resp.status_code != 200:
            raise RiotAPIError(resp.status_code, resp.text)
        data = resp.json()
        cache.set(cache_key, data, ttl=ttl)
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

    # --- League-V4 (platform) ---
    async def league_entries(self, platform: str, summoner_id: str):
        return await self._get(
            platform,
            f"/lol/league/v4/entries/by-summoner/{summoner_id}",
            ttl=300,
            cache_key=f"league:{platform}:{summoner_id}",
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
    async def match_ids(self, region_cluster: str, puuid: str, count: int = 20):
        return await self._get(
            region_cluster,
            f"/lol/match/v5/matches/by-puuid/{puuid}/ids?count={count}",
            ttl=120,
            cache_key=f"matchids:{region_cluster}:{puuid}:{count}",
        )

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
    entries = await client.league_entries(platform, summoner["id"])
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
