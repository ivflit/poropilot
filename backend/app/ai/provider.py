"""AI provider selection and dispatch.

Picks the AI backend from config and routes the draft/patch calls to it. The
backend clients are constructed lazily (only when a call is made), so importing
this module never requires an API key.
"""

from app.ai import draft, gemini, review, tierlist
from app.ai import patch as anthropic_patch
from app.config import settings

ANTHROPIC = "anthropic"
GEMINI = "gemini"


def _provider_key(provider: str) -> str:
    """The configured API key for a provider name ("" when there isn't one)."""
    if provider == ANTHROPIC:
        return settings.anthropic_api_key
    if provider == GEMINI:
        return settings.gemini_api_key
    return ""


def active_provider() -> str | None:
    """The AI provider in use, or None if AI is off.

    Explicit AI_PROVIDER wins; otherwise auto-detect from whichever key is set
    (Anthropic preferred). None means AI is disabled.

    A provider is only "active" if its key is actually set. Naming a provider
    without its key used to report AI as enabled, so the UI showed the draft
    board and the endpoints failed mid-call instead of returning a clean 503.
    """
    explicit = settings.ai_provider.strip().lower()
    if explicit:
        return explicit if _provider_key(explicit) else None
    if settings.anthropic_api_key:
        return ANTHROPIC
    if settings.gemini_api_key:
        return GEMINI
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


def review_match(stats: dict) -> dict:
    if active_provider() == "gemini":
        return review.review_match_gemini(stats)
    return review.review_match_anthropic(stats)


def generate_tier_list(role: str, patch: str) -> dict:
    if active_provider() == "gemini":
        return tierlist.tier_list_gemini(role, patch)
    return tierlist.tier_list_anthropic(role, patch)
