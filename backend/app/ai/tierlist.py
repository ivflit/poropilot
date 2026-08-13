"""AI-generated champion tier list per role.

Uses the same provider-agnostic pattern as the draft and review modules.
Tier lists are cached per patch + role so the AI is only called once per combination.
"""

import json

from app.config import settings

_INSTRUCTION = (
    "You are a League of Legends meta analyst. For the given role in the current patch, "
    "rank the strongest champions into tiers: S (must-ban/pick), A (strong), B (viable), "
    "C (niche/situational). Include 3-5 champions per tier. For each champion, give a "
    "one-sentence reason why they're in that tier. Be current, concise, and grounded in "
    "the meta. Return JSON only."
)

_SCHEMA = {
    "type": "object",
    "properties": {
        "tiers": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "tier": {"type": "string", "enum": ["S", "A", "B", "C"]},
                    "champions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "reason": {"type": "string"},
                            },
                            "required": ["name", "reason"],
                        },
                    },
                },
                "required": ["tier", "champions"],
            },
        },
    },
    "required": ["tiers"],
}


_anthropic_client = None


def _get_anthropic():
    global _anthropic_client
    if _anthropic_client is None:
        import anthropic
        _anthropic_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    return _anthropic_client


def tier_list_anthropic(role: str, patch: str) -> dict:
    client = _get_anthropic()
    prompt = f"Role: {role}\nPatch: {patch}\n\nGenerate the tier list."
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        system=_INSTRUCTION + f"\n\nRespond with JSON matching this schema:\n{json.dumps(_SCHEMA)}",
        messages=[{"role": "user", "content": prompt}],
    )
    text = response.content[0].text
    start = text.find("{")
    end = text.rfind("}") + 1
    return json.loads(text[start:end])


def tier_list_gemini(role: str, patch: str) -> dict:
    from google import genai
    from google.genai.types import GenerateContentConfig

    client = genai.Client(api_key=settings.gemini_api_key)
    prompt = f"Role: {role}\nPatch: {patch}\n\nGenerate the tier list."
    response = client.models.generate_content(
        model=settings.gemini_model,
        contents=prompt,
        config=GenerateContentConfig(
            system_instruction=_INSTRUCTION,
            response_mime_type="application/json",
            response_schema=_SCHEMA,
        ),
    )
    return json.loads(response.text)
