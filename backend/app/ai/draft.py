"""AI draft assistant — recommends a champion pick from the player's pool.

Uses the Anthropic Claude API with structured outputs so the frontend receives
clean, validated JSON. Model is configurable via ANTHROPIC_MODEL (see config).
"""

import json

import anthropic

from app.config import settings

_client = None


def _get_client() -> "anthropic.Anthropic":
    # Built lazily so the app imports fine without an ANTHROPIC_API_KEY — the
    # AI endpoints guard on the key before ever calling this.
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


_SYSTEM = (
    "You are a League of Legends draft coach. Given the player's role, champion pool, "
    "allied picks, enemy bans and enemy picks, recommend up to 4 champions for the role. "
    "Prefer champions from the player's pool when they're a good fit and mark those "
    "in_pool=true. If the pool is empty or a poor fit for this matchup, also suggest "
    "strong picks for the role that are NOT in the pool (in_pool=false) so the player "
    "knows good options to consider. Explain each pick briefly — synergy with allies, "
    "matchup, and how it fares against the enemy picks. Be concise and concrete."
)

_SCHEMA = {
    "type": "object",
    "properties": {
        "suggestions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "champion": {"type": "string"},
                    "reason": {"type": "string"},
                    "confidence": {"type": "string", "enum": ["low", "medium", "high"]},
                    "in_pool": {"type": "boolean"},
                },
                "required": ["champion", "reason", "confidence", "in_pool"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["suggestions"],
    "additionalProperties": False,
}


def suggest_pick(
    role: str,
    champion_pool: list[str],
    ally_picks: list[str],
    enemy_bans: list[str],
    enemy_picks: list[str] | None = None,
) -> dict:
    context = (
        f"Role: {role}\n"
        f"My champion pool: {', '.join(champion_pool) or '(none given)'}\n"
        f"Allied picks: {', '.join(ally_picks) or '(none)'}\n"
        f"Enemy bans: {', '.join(enemy_bans) or '(none)'}\n"
        f"Enemy picks: {', '.join(enemy_picks or []) or '(none)'}\n\n"
        "Recommend up to 4 champions for this role, best first — prefer my pool, but "
        "include strong out-of-pool options if my pool is empty or a weak fit."
    )

    resp = _get_client().messages.create(
        model=settings.anthropic_model,
        max_tokens=1024,
        system=[{"type": "text", "text": _SYSTEM, "cache_control": {"type": "ephemeral"}}],
        output_config={"format": {"type": "json_schema", "schema": _SCHEMA}},
        messages=[{"role": "user", "content": context}],
    )

    text = next(block.text for block in resp.content if block.type == "text")
    return json.loads(text)
