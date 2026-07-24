"""AI provider selection and dispatch.

Picks the AI backend from config and routes the draft/patch calls to it. The
backend clients are constructed lazily (only when a call is made), so importing
this module never requires an API key.
"""

from app.ai import draft, gemini
from app.ai import patch as anthropic_patch
from app.config import settings


def active_provider() -> str | None:
    """The AI provider in use, or None if AI is off.

    Explicit AI_PROVIDER wins; otherwise auto-detect from whichever key is set
    (Anthropic preferred). None means no key configured → AI disabled.
    """
    if settings.ai_provider:
        return settings.ai_provider
    if settings.anthropic_api_key:
        return "anthropic"
    if settings.gemini_api_key:
        return "gemini"
    return None


def ai_enabled() -> bool:
    return active_provider() is not None


def suggest_pick(**kwargs) -> dict:
    if active_provider() == "gemini":
        return gemini.suggest_pick(**kwargs)
    return draft.suggest_pick(**kwargs)


def patch_digest(champions: list[str], patch: str) -> dict:
    if active_provider() == "gemini":
        return gemini.patch_digest(champions, patch)
    return anthropic_patch.patch_digest(champions, patch)
