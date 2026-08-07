"""Match history detail extraction — turns a raw Match-V5 blob into a rich MatchDetail.

Pure functions, no I/O, easy to test against fixture data.
"""

from enum import StrEnum

from app.schemas import MatchDetail, MatchParticipant


class MatchRole(StrEnum):
    ALL = "all"
    TOP = "TOP"
    JUNGLE = "JUNGLE"
    MIDDLE = "MIDDLE"
    BOTTOM = "BOTTOM"
    UTILITY = "UTILITY"


class MatchResult(StrEnum):
    ALL = "all"
    WIN = "win"
    LOSS = "loss"


class MatchSort(StrEnum):
    NEWEST = "newest"
    OLDEST = "oldest"
    CS_MIN = "cs_min"
    DMG_MIN = "dmg_min"


# Riot's position strings → friendly short labels.
ROLE_LABELS = {
    "TOP": "Top",
    "JUNGLE": "Jng",
    "MIDDLE": "Mid",
    "BOTTOM": "ADC",
    "UTILITY": "Sup",
}


def _player_role(participant: dict) -> str:
    """Best-effort role from the participant blob."""
    return participant.get("teamPosition") or participant.get("individualPosition") or ""


def _find_opponent(participants: list[dict], player: dict) -> str:
    """Find the opponent in the same role on the other team."""
    role = _player_role(player)
    team = player.get("teamId", 0)
    if not role:
        return ""
    for p in participants:
        if p.get("teamId") != team and _player_role(p) == role:
            return p.get("championName", "")
    return ""


def build_match_detail(match: dict, puuid: str) -> MatchDetail | None:
    """Extract a MatchDetail for the given PUUID from a Match-V5 blob.

    Returns None if the player isn't in the match.
    """
    info = match.get("info", {})
    participants = info.get("participants", [])

    player = None
    for p in participants:
        if p.get("puuid") == puuid:
            player = p
            break
    if player is None:
        return None

    duration_sec = info.get("gameDuration", 0)
    duration_min = duration_sec / 60 if duration_sec else 0
    cs = player.get("totalMinionsKilled", 0) + player.get("neutralMinionsKilled", 0)
    damage = player.get("totalDamageDealtToChampions", 0)

    all_participants = []
    for p in participants:
        all_participants.append(MatchParticipant(
            champion=p.get("championName", "?"),
            team_id=p.get("teamId", 0),
        ))

    return MatchDetail(
        match_id=match.get("metadata", {}).get("matchId", ""),
        champion=player.get("championName", "?"),
        win=player.get("win", False),
        kills=player.get("kills", 0),
        deaths=player.get("deaths", 0),
        assists=player.get("assists", 0),
        cs=cs,
        cs_per_min=round(cs / duration_min, 1) if duration_min else 0,
        damage=damage,
        damage_per_min=round(damage / duration_min, 0) if duration_min else 0,
        gold=player.get("goldEarned", 0),
        vision_score=player.get("visionScore", 0),
        role=_player_role(player),
        opponent_champion=_find_opponent(participants, player),
        queue_id=info.get("queueId", 0),
        duration_min=round(duration_min, 1),
        game_start=info.get("gameStartTimestamp", 0) // 1000,
        participants=all_participants,
    )
