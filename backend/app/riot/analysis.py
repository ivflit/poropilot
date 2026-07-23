"""Champion-pool analysis — aggregate Match-V5 detail into per-champion stats.

A Match-V5 match holds an `info.participants` list; we pick out the row for the
PUUID we're analysing and fold its numbers into a running per-champion tally.
Everything here is pure and synchronous so the maths is trivially testable over
a fixture match set.
"""

from ..schemas import ChampionStats


def _participant(match: dict, puuid: str) -> dict | None:
    """The match participant row for `puuid`, or None if they aren't in it."""
    for participant in match.get("info", {}).get("participants", []):
        if participant.get("puuid") == puuid:
            return participant
    return None


def _cs(participant: dict) -> int:
    """Total creep score — lane minions plus jungle/neutral monsters."""
    return participant.get("totalMinionsKilled", 0) + participant.get("neutralMinionsKilled", 0)


def aggregate_champion_stats(matches: list[dict], puuid: str) -> list[ChampionStats]:
    """Fold a PUUID's matches into per-champion games/wins/KDA/CS-per-min.

    Matches missing the PUUID (e.g. a shared page) are skipped. Games with no
    duration don't contribute to CS/min but still count towards games and KDA.
    Results are sorted by games played, then champion id, for a stable order.
    """
    tallies: dict[int, dict] = {}
    for match in matches:
        participant = _participant(match, puuid)
        if participant is None:
            continue

        champion_id = participant.get("championId", 0)
        tally = tallies.setdefault(
            champion_id,
            {
                "champion_name": participant.get("championName", ""),
                "games": 0,
                "wins": 0,
                "kills": 0,
                "deaths": 0,
                "assists": 0,
                "cs": 0,
                "minutes": 0.0,
            },
        )

        tally["games"] += 1
        tally["wins"] += 1 if participant.get("win") else 0
        tally["kills"] += participant.get("kills", 0)
        tally["deaths"] += participant.get("deaths", 0)
        tally["assists"] += participant.get("assists", 0)
        tally["cs"] += _cs(participant)
        tally["minutes"] += match.get("info", {}).get("gameDuration", 0) / 60

    stats = [
        ChampionStats(
            champion_id=champion_id,
            champion_name=tally["champion_name"],
            games=tally["games"],
            wins=tally["wins"],
            win_rate=round(tally["wins"] / tally["games"], 4),
            avg_kda=round((tally["kills"] + tally["assists"]) / max(tally["deaths"], 1), 2),
            avg_cs_per_min=round(tally["cs"] / tally["minutes"], 2) if tally["minutes"] else 0.0,
        )
        for champion_id, tally in tallies.items()
    ]
    stats.sort(key=lambda s: (-s.games, s.champion_id))
    return stats
