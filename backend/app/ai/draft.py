"""AI draft assistant — recommends a champion pick from the player's pool.

Uses the Anthropic Claude API with structured outputs so the frontend receives
clean, validated JSON. Model is configurable via ANTHROPIC_MODEL (see config).
"""

import json

import anthropic

from ..config import settings

_client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment

_SYSTEM = (
    "You are a League of Legends draft coach. Given the player's role, their champion "
    "pool, their allies' picks and the enemy bans/picks, recommend the best champions "
    "for the player to pick FROM THEIR OWN POOL. Consider team composition, matchups and "
    "the current meta. Be concise and concrete."
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
                },
                "required": ["champion", "reason", "confidence"],
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
        "Recommend up to 3 champions from my pool, best first."
    )

    resp = _client.messages.create(
        model=settings.anthropic_model,
        max_tokens=1024,
        system=[{"type": "text", "text": _SYSTEM, "cache_control": {"type": "ephemeral"}}],
        output_config={"format": {"type": "json_schema", "schema": _SCHEMA}},
        messages=[{"role": "user", "content": context}],
    )

    text = next(block.text for block in resp.content if block.type == "text")
    return json.loads(text)
