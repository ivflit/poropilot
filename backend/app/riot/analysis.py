"""Champion-pool analysis — aggregate Match-V5 detail into per-champion stats.

A Match-V5 match holds an `info.participants` list; we pick out the row for the
PUUID we're analysing and fold its numbers into a running per-champion tally.
Everything here is pure and synchronous so the maths is trivially testable over
a fixture match set.
"""

import math

from app.schemas import ChampionStats

WILSON_Z = 1.96  # z for a 95% confidence interval


def _wilson_lower_bound(wins: int, games: int) -> float:
    """Lower bound of the Wilson score interval for a win proportion.

    Ranking on raw win-rate lets a 1-of-1 (100%) champion outrank a proven
    12-of-20 (60%) one. The Wilson lower bound discounts small samples, so more
    games on a champion earn a higher, better-evidenced score — 0.0 with no games.
    """
    if games <= 0:
        return 0.0
    p = wins / games
    z = WILSON_Z
    denominator = 1 + z**2 / games
    centre = p + z**2 / (2 * games)
    margin = z * math.sqrt((p * (1 - p) + z**2 / (4 * games)) / games)
    return (centre - margin) / denominator


def _form_score(wins: int, games: int, avg_kda: float) -> float:
    """A 0..1-ish "form" score: recent win confidence nudged by KDA.

    Win confidence (the Wilson lower bound) is the backbone; a bounded KDA factor
    (1.0..1.5) breaks ties so a champion carried by strong individual play ranks
    above an equal win-rate with worse KDA.
    """
    confidence = _wilson_lower_bound(wins, games)
    kda_factor = 1 + min(avg_kda, 6.0) / 12
    return round(confidence * kda_factor, 4)


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

    stats = []
    for champion_id, tally in tallies.items():
        avg_kda = round((tally["kills"] + tally["assists"]) / max(tally["deaths"], 1), 2)
        stats.append(
            ChampionStats(
                champion_id=champion_id,
                champion_name=tally["champion_name"],
                games=tally["games"],
                wins=tally["wins"],
                win_rate=round(tally["wins"] / tally["games"], 4),
                avg_kda=avg_kda,
                avg_cs_per_min=round(tally["cs"] / tally["minutes"], 2) if tally["minutes"] else 0.0,
                form_score=_form_score(tally["wins"], tally["games"], avg_kda),
            )
        )
    stats.sort(key=lambda s: (-s.games, s.champion_id))
    return stats


def top_champions(stats: list[ChampionStats], limit: int = 5) -> list[ChampionStats]:
    """The player's strongest recent champions, best form first.

    Ties on form fall back to more games then champion id, for a stable order.
    """
    ranked = sorted(stats, key=lambda s: (-s.form_score, -s.games, s.champion_id))
    return ranked[:limit]
