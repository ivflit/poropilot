"""Champion static data from Riot's Data Dragon CDN.

Data Dragon needs no API key. We fetch the current version and the champion
dataset once, build an id -> Champion map, and hold it in memory so we never
call the CDN per request. `build_champion_map` is kept pure so it can be tested
against a stubbed dataset without any network access.
"""

import httpx

from app.schemas import Champion

DDRAGON = "https://ddragon.leagueoflegends.com"


def build_champion_map(version: str, champion_data: dict) -> dict[int, Champion]:
    """Turn a Data Dragon champion.json `data` block into an id -> Champion map."""
    champions: dict[int, Champion] = {}
    for entry in champion_data.values():
        champion_id = int(entry["key"])
        champions[champion_id] = Champion(
            champion_id=champion_id,
            name=entry["name"],
            title=entry["title"],
            image_url=f"{DDRAGON}/cdn/{version}/img/champion/{entry['image']['full']}",
        )
    return champions


class ChampionService:
    def __init__(self, http: httpx.AsyncClient) -> None:
        self._http = http

    async def latest_version(self) -> str:
        resp = await self._http.get(f"{DDRAGON}/api/versions.json")
        resp.raise_for_status()
        return resp.json()[0]

    async def load(self) -> tuple[str, dict[int, Champion]]:
        """Fetch the current version + champion dataset and build the map."""
        version = await self.latest_version()
        resp = await self._http.get(f"{DDRAGON}/cdn/{version}/data/en_US/champion.json")
        resp.raise_for_status()
        data = resp.json()["data"]
        return version, build_champion_map(version, data)
