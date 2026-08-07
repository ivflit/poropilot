"""Pydantic models — request/response schemas (RORO: receive an object, return an object)."""

from pydantic import BaseModel

from app.riot.queues import MatchQueue


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
    in_pool: bool = True  # whether the pick is from the player's own champion pool


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
    form_score: float  # 0..1-ish "recent form" — win confidence nudged by KDA


class PatchNote(BaseModel):
    champion: str
    summary: str


class PatchDigest(BaseModel):
    patch: str
    notes: list[PatchNote]


class ChampionPool(BaseModel):
    """A player's recent champion pool, folded from their match history.

    Empty lists are a valid, non-error result — a player with few or no games
    simply has a small (or empty) pool.
    """

    queue: MatchQueue = MatchQueue.ALL  # which filter these numbers were computed over
    total_games: int
    champions: list[ChampionStats]
    top: list[ChampionStats]


class MatchParticipant(BaseModel):
    champion: str
    team_id: int
    kills: int = 0
    deaths: int = 0
    assists: int = 0
    cs: int = 0
    damage: int = 0
    gold: int = 0


class MatchSummary(BaseModel):
    match_id: str
    champion: str
    win: bool
    kills: int
    deaths: int
    assists: int
    queue_id: int
    duration_min: float


class MatchDetail(BaseModel):
    match_id: str
    champion: str
    win: bool
    kills: int
    deaths: int
    assists: int
    cs: int
    cs_per_min: float
    damage: int
    damage_per_min: float
    gold: int
    vision_score: int
    role: str
    opponent_champion: str
    queue_id: int
    duration_min: float
    game_start: int  # epoch seconds
    participants: list[MatchParticipant]


class AggregateStats(BaseModel):
    wins: int
    losses: int
    win_rate: float  # 0..1
    avg_kills: float
    avg_deaths: float
    avg_assists: float
    kda_ratio: float  # (kills + assists) / deaths


class MatchHistoryResponse(BaseModel):
    matches: list[MatchDetail]
    total_fetched: int
    aggregate: AggregateStats


class MultiSearchRequest(BaseModel):
    region: str
    riot_ids: list[str]  # ["name#tag", ...]


class MultiSearchPlayer(BaseModel):
    riot_id: str
    found: bool
    region: str | None = None
    level: int | None = None
    profile_icon_id: int | None = None
    ranked: list[dict] = []
    top_champions: list[ChampionStats] = []


class MultiSearchResponse(BaseModel):
    players: list[MultiSearchPlayer]


class ReviewIssue(BaseModel):
    point: str
    stat: str


class MatchReview(BaseModel):
    match_id: str
    champion: str
    win: bool
    verdict: str
    issues: list[ReviewIssue]
    tips: list[str]
