"""AI patch digest — summarise the latest patch for a set of champions.

Uses Claude with web search to fetch current patch notes (they aren't in the Riot
API), then returns a per-champion summary as structured JSON. Model configurable
via ANTHROPIC_MODEL.
"""

import json

import anthropic

from ..config import settings

_client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment

_SYSTEM = (
    "You summarise League of Legends patch notes. Given a patch version and a list of "
    "champions, return a short, factual summary of what changed for EACH champion in "
    "that patch (buffs, nerfs, adjustments). If a champion was untouched, say so plainly."
)

_SCHEMA = {
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
                "additionalProperties": False,
            },
        }
    },
    "required": ["notes"],
    "additionalProperties": False,
}


def patch_digest(champions: list[str], patch: str, client=None) -> dict:
    """Summarise `patch` for `champions`. Returns {"patch", "notes": [...]}.

    `client` is injectable so tests can stub the Anthropic call.
    """
    client = client or _client
    prompt = (
        f"League of Legends patch {patch}. Summarise what changed for these "
        f"champions: {', '.join(champions)}."
    )
    resp = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=1500,
        system=[{"type": "text", "text": _SYSTEM, "cache_control": {"type": "ephemeral"}}],
        tools=[{"type": "web_search_20260209", "name": "web_search"}],
        output_config={"format": {"type": "json_schema", "schema": _SCHEMA}},
        messages=[{"role": "user", "content": prompt}],
    )
    text = next(block.text for block in resp.content if block.type == "text")
    return {"patch": patch, "notes": json.loads(text)["notes"]}
