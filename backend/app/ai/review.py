"""Post-game review — derives stats from a match and feeds them to the AI.

The AI receives only **derived** numbers, never the raw match blob, so every
piece of advice is grounded in a stat we actually computed. The stat derivation
is pure and synchronous for easy testing; the AI call is provider-agnostic.
"""

import json

from app.config import settings

# ── Stat derivation (pure, testable) ───────────────────────────────────────────

RANKED_QUEUES = {420, 440}  # solo/duo and flex


def is_ranked(match: dict) -> bool:
    return match.get("info", {}).get("queueId") in RANKED_QUEUES


def _find_participant(match: dict, puuid: str) -> dict | None:
    for p in match.get("info", {}).get("participants", []):
        if p.get("puuid") == puuid:
            return p
    return None


def _find_lane_opponent(match: dict, player: dict) -> dict | None:
    """Find the enemy in the same individual position."""
    team_id = player.get("teamId")
    position = player.get("individualPosition") or player.get("teamPosition")
    if not position:
        return None
    for p in match.get("info", {}).get("participants", []):
        if p.get("teamId") != team_id:
            opponent_pos = p.get("individualPosition") or p.get("teamPosition")
            if opponent_pos == position:
                return p
    return None


def _cs(p: dict) -> int:
    return p.get("totalMinionsKilled", 0) + p.get("neutralMinionsKilled", 0)


def _team_stats(match: dict, team_id: int) -> dict:
    """Aggregate team totals for damage share and objective participation."""
    total_damage = 0
    total_kills = 0
    for p in match.get("info", {}).get("participants", []):
        if p.get("teamId") == team_id:
            total_damage += p.get("totalDamageDealtToChampions", 0)
            total_kills += p.get("kills", 0)
    return {"total_damage": total_damage, "total_kills": total_kills}


def derive_stats(match: dict, puuid: str) -> dict | None:
    """Extract coaching-relevant stats from a match for a specific player.

    Returns None if the player isn't in the match.
    """
    player = _find_participant(match, puuid)
    if not player:
        return None

    duration_min = match.get("info", {}).get("gameDuration", 0) / 60
    if duration_min < 1:
        return None

    kills = player.get("kills", 0)
    deaths = player.get("deaths", 0)
    assists = player.get("assists", 0)
    kda = round((kills + assists) / max(deaths, 1), 2)
    cs = _cs(player)
    cs_per_min = round(cs / duration_min, 1)

    team = _team_stats(match, player.get("teamId", 0))
    damage = player.get("totalDamageDealtToChampions", 0)
    damage_share = round(damage / max(team["total_damage"], 1) * 100, 1)
    kill_participation = round(
        (kills + assists) / max(team["total_kills"], 1) * 100, 1
    )

    vision = player.get("visionScore", 0)
    vision_per_min = round(vision / duration_min, 1)

    opponent = _find_lane_opponent(match, player)
    opponent_stats = None
    if opponent:
        opp_cs = _cs(opponent)
        opponent_stats = {
            "champion": opponent.get("championName", "?"),
            "kills": opponent.get("kills", 0),
            "deaths": opponent.get("deaths", 0),
            "cs_diff": cs - opp_cs,
            "gold_diff": player.get("goldEarned", 0) - opponent.get("goldEarned", 0),
        }

    return {
        "champion": player.get("championName", "?"),
        "role": player.get("individualPosition") or player.get("teamPosition") or "?",
        "win": player.get("win", False),
        "kills": kills,
        "deaths": deaths,
        "assists": assists,
        "kda": kda,
        "cs": cs,
        "cs_per_min": cs_per_min,
        "damage": damage,
        "damage_share": damage_share,
        "kill_participation": kill_participation,
        "vision_score": vision,
        "vision_per_min": vision_per_min,
        "game_duration_min": round(duration_min, 1),
        "opponent": opponent_stats,
    }


# ── AI prompt ──────────────────────────────────────────────────────────────────

_SYSTEM = (
    "You are a League of Legends coach reviewing a player's recent ranked game. "
    "You receive derived stats — ground EVERY point in a specific number from the stats. "
    "Never invent facts. Be direct, honest and constructive.\n\n"
    "Return JSON with:\n"
    "- verdict: one-line summary of the game (10-15 words)\n"
    "- issues: array of 2-4 objects, each {point, stat} where point is what went wrong "
    "and stat is the exact number backing it\n"
    "- tips: array of 2-3 concrete, actionable things to do next game"
)

_SCHEMA = {
    "type": "object",
    "properties": {
        "verdict": {"type": "string"},
        "issues": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "point": {"type": "string"},
                    "stat": {"type": "string"},
                },
                "required": ["point", "stat"],
            },
        },
        "tips": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "required": ["verdict", "issues", "tips"],
}


def _format_stats(stats: dict) -> str:
    lines = [
        f"Champion: {stats['champion']} ({stats['role']})",
        f"Result: {'Win' if stats['win'] else 'Loss'}",
        f"KDA: {stats['kills']}/{stats['deaths']}/{stats['assists']} ({stats['kda']})",
        f"CS: {stats['cs']} ({stats['cs_per_min']}/min)",
        f"Damage: {stats['damage']:,} ({stats['damage_share']}% of team)",
        f"Kill participation: {stats['kill_participation']}%",
        f"Vision: {stats['vision_score']} ({stats['vision_per_min']}/min)",
        f"Game length: {stats['game_duration_min']} min",
    ]
    if stats.get("opponent"):
        opp = stats["opponent"]
        lines.append(
            f"Lane opponent: {opp['champion']} — "
            f"CS diff: {opp['cs_diff']:+d}, Gold diff: {opp['gold_diff']:+d}"
        )
    return "\n".join(lines)


def review_match_anthropic(stats: dict) -> dict:
    import anthropic

    client = anthropic.Anthropic()
    resp = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=1024,
        system=[{"type": "text", "text": _SYSTEM}],
        output_config={"format": {"type": "json_schema", "schema": _SCHEMA}},
        messages=[{"role": "user", "content": _format_stats(stats)}],
    )
    text = next(block.text for block in resp.content if block.type == "text")
    return json.loads(text)


def review_match_gemini(stats: dict, client=None) -> dict:
    from google import genai

    if client is None:
        client = genai.Client(api_key=settings.gemini_api_key)
    interaction = client.interactions.create(
        model=settings.gemini_model,
        input=f"{_SYSTEM}\n\n{_format_stats(stats)}",
        response_format={"type": "text", "mime_type": "application/json", "schema": _SCHEMA},
    )
    return json.loads(interaction.output_text)
