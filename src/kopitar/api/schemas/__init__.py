"""
API Schemas

Pydantic models for API request/response validation.
"""

from .common import (
    PaginationParams, SeasonParam, ErrorResponse, SuccessResponse,
    MetricsFilter, PositionFilter, SeasonFilter, CacheControl,
    AnalyticsParams, SortParams, DateRangeParams
)
from .players import (
    PlayerResponse, PlayerStatsResponse, PlayerFatigueResponse,
    PlayerSearchRequest, PlayerComparisonResponse, Position
)
from .teams import (
    TeamResponse, TeamStatsResponse, TeamScheduleResponse,
    VenueInfo, DivisionInfo, ConferenceInfo
)
from .games import (
    GameResponse, GameStatsResponse, GameSearchRequest,
    GamePrediction, GameAnalysis, GameState, GameType
)

__all__ = [
    # Common
    "PaginationParams",
    "SeasonParam", 
    "ErrorResponse",
    "SuccessResponse",
    "MetricsFilter",
    "PositionFilter",
    "SeasonFilter",
    "CacheControl",
    "AnalyticsParams",
    "SortParams",
    "DateRangeParams",
    
    # Players
    "PlayerResponse",
    "PlayerStatsResponse",
    "PlayerFatigueResponse",
    "PlayerSearchRequest",
    "PlayerComparisonResponse",
    "Position",
    
    # Teams
    "TeamResponse",
    "TeamStatsResponse",
    "TeamScheduleResponse",
    "VenueInfo",
    "DivisionInfo",
    "ConferenceInfo",
    
    # Games
    "GameResponse",
    "GameStatsResponse",
    "GameSearchRequest",
    "GamePrediction",
    "GameAnalysis",
    "GameState",
    "GameType",
]