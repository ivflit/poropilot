"""Gemini AI backend — draft assistant + patch digest via Google's Gemini API.

Uses the google-genai SDK's Interactions API with JSON structured output. The
client is built lazily (and is injectable for tests) so the app imports fine
without a key. Mirrors the shapes returned by the Anthropic backend.
"""

import json

from google import genai

from app.config import settings

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


_DRAFT_INSTRUCTION = (
    "You are a League of Legends draft coach. Given the player's role, champion pool, "
    "allied picks, enemy bans and enemy picks, recommend up to 4 champions for the role. "
    "Prefer champions from the player's pool when they're a good fit and mark those "
    "in_pool=true. If the pool is empty or a poor fit, also suggest strong picks for the "
    "role that are NOT in the pool (in_pool=false). Briefly explain each pick — synergy, "
    "matchup, and how it fares against the enemy picks. Be concise."
)

_DRAFT_SCHEMA = {
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
            },
        }
    },
    "required": ["suggestions"],
}

_PATCH_INSTRUCTION = (
    "You summarise League of Legends patch notes. Given a patch version and a list of "
    "champions, return a short, factual summary of what changed for EACH champion in "
    "that patch. If a champion was untouched, say so plainly."
)

_PATCH_SCHEMA = {
    "type": "object",
    "properties": {
        "notes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "champion": {"type": "string"},
                    "summary": {"type": "string"},
                },
                "required": ["champion", "summary"],
            },
        }
    },
    "required": ["notes"],
}


def _generate(instruction: str, prompt: str, schema: dict, client=None) -> dict:
    client = client or _get_client()
    interaction = client.interactions.create(
        model=settings.gemini_model,
        input=f"{instruction}\n\n{prompt}",
        response_format={"type": "text", "mime_type": "application/json", "schema": schema},
    )
    return json.loads(interaction.output_text)


def suggest_pick(
    role: str,
    champion_pool: list[str],
    ally_picks: list[str],
    enemy_bans: list[str],
    enemy_picks: list[str] | None = None,
    client=None,
) -> dict:
    prompt = (
        f"Role: {role}\n"
        f"My champion pool: {', '.join(champion_pool) or '(none given)'}\n"
        f"Allied picks: {', '.join(ally_picks) or '(none)'}\n"
        f"Enemy bans: {', '.join(enemy_bans) or '(none)'}\n"
        f"Enemy picks: {', '.join(enemy_picks or []) or '(none)'}\n\n"
        "Recommend up to 4 champions for this role, best first — prefer my pool, but "
        "include strong out-of-pool options if my pool is empty or a weak fit."
    )
    return _generate(_DRAFT_INSTRUCTION, prompt, _DRAFT_SCHEMA, client=client)


def patch_digest(champions: list[str], patch: str, client=None) -> dict:
    prompt = f"Patch {patch}. Summarise what changed for: {', '.join(champions)}."
    result = _generate(_PATCH_INSTRUCTION, prompt, _PATCH_SCHEMA, client=client)
    return {"patch": patch, "notes": result["notes"]}
