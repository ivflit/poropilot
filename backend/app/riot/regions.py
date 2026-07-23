"""Riot region routing.

Riot splits its APIs across two kinds of host:
- **Platform** hosts (e.g. euw1) for Summoner-V4, League-V4, Champion-Mastery-V4.
- **Regional** clusters (americas / asia / europe) for Account-V1 and Match-V5.
"""

# User-facing region code -> platform host
PLATFORMS: dict[str, str] = {
    "NA": "na1",
    "EUW": "euw1",
    "EUNE": "eun1",
    "KR": "kr",
    "BR": "br1",
    "JP": "jp1",
    "LAN": "la1",
    "LAS": "la2",
    "OCE": "oc1",
    "TR": "tr1",
    "RU": "ru",
}

# Platform host -> regional cluster (for Account-V1 / Match-V5)
_PLATFORM_TO_REGION: dict[str, str] = {
    "na1": "americas",
    "br1": "americas",
    "la1": "americas",
    "la2": "americas",
    "oc1": "americas",
    "kr": "asia",
    "jp1": "asia",
    "euw1": "europe",
    "eun1": "europe",
    "tr1": "europe",
    "ru": "europe",
}


class UnknownRegionError(ValueError):
    pass


def platform_host(region_code: str) -> str:
    """'EUW' -> 'euw1'. Raises UnknownRegionError for unrecognised codes."""
    try:
        return PLATFORMS[region_code.upper()]
    except KeyError as exc:
        raise UnknownRegionError(f"Unknown region: {region_code!r}") from exc


def regional_route(platform: str) -> str:
    """'euw1' -> 'europe'. Raises UnknownRegionError for unrecognised platforms."""
    try:
        return _PLATFORM_TO_REGION[platform]
    except KeyError as exc:
        raise UnknownRegionError(f"Unknown platform: {platform!r}") from exc
