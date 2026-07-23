"""Pydantic models — request/response schemas (RORO: receive an object, return an object)."""

from pydantic import BaseModel


class MasteryEntry(BaseModel):
    champion_id: int
    points: int
    level: int


class Profile(BaseModel):
    riot_id: str
    region: str
    level: int | None
    profile_icon_id: int | None
    ranked: list[dict]
    top_masteries: list[MasteryEntry]


class DraftRequest(BaseModel):
    role: str
    champion_pool: list[str]
    ally_picks: list[str] = []
    enemy_bans: list[str] = []
    enemy_picks: list[str] = []


class Suggestion(BaseModel):
    champion: str
    reason: str
    confidence: str


class DraftResponse(BaseModel):
    suggestions: list[Suggestion]


class Champion(BaseModel):
    champion_id: int
    name: str
    title: str
    image_url: str


class ChampionStats(BaseModel):
    """Per-champion aggregate over a set of recent matches."""

    champion_id: int
    champion_name: str
    games: int
    wins: int
    win_rate: float  # 0..1
    avg_kda: float  # (kills + assists) / deaths, deaths floored at 1
    avg_cs_per_min: float
