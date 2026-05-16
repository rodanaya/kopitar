"""
Player API Schemas

Pydantic models for player-related requests and responses.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel, Field, validator
from enum import Enum

from .common import PaginationParams, MetricsFilter


class Position(str, Enum):
    """Player position enumeration."""
    GOALIE = "G"
    DEFENSE = "D" 
    FORWARD = "F"


class PlayerSearchRequest(BaseModel):
    """Request model for player search."""
    
    query: str = Field(..., min_length=2, description="Search query")
    position: Optional[Position] = Field(None, description="Filter by position")
    team_id: Optional[int] = Field(None, description="Filter by team")
    active_only: bool = Field(True, description="Only active players")
    limit: int = Field(20, ge=1, le=100, description="Maximum results")


class PlayerBasicInfo(BaseModel):
    """Basic player information."""
    
    id: int = Field(..., description="NHL Player ID")
    full_name: str = Field(..., description="Player's full name")
    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")
    birth_date: Optional[date] = Field(None, description="Date of birth")
    birth_city: Optional[str] = Field(None, description="Birth city")
    birth_country: Optional[str] = Field(None, description="Birth country")
    nationality: Optional[str] = Field(None, description="Nationality")
    height: Optional[str] = Field(None, description="Height (e.g., '6-2')")
    weight: Optional[int] = Field(None, description="Weight in pounds")
    position: Position = Field(..., description="Player position")
    shoots_catches: Optional[str] = Field(None, description="Shooting/catching hand")
    
    @property
    def age(self) -> Optional[int]:
        """Calculate current age."""
        if self.birth_date:
            today = date.today()
            return today.year - self.birth_date.year - (
                (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
            )
        return None


class TeamInfo(BaseModel):
    """Team information for player."""
    
    id: int = Field(..., description="Team ID")
    name: str = Field(..., description="Team name")
    abbreviation: str = Field(..., description="Team abbreviation")
    division: Optional[str] = Field(None, description="Division name")
    conference: Optional[str] = Field(None, description="Conference name")


class PlayerResponse(PlayerBasicInfo):
    """Complete player response with team info."""
    
    current_team: Optional[TeamInfo] = Field(None, description="Current team")
    active: bool = Field(True, description="Is player active")
    rookie: bool = Field(False, description="Is rookie")
    captain: bool = Field(False, description="Is team captain")
    alternate_captain: bool = Field(False, description="Is alternate captain")
    
    # Career summary
    nhl_debut: Optional[date] = Field(None, description="NHL debut date")
    seasons_played: Optional[int] = Field(None, description="Seasons in NHL")
    games_played: Optional[int] = Field(None, description="Career games played")
    
    # URLs and links
    headshot_url: Optional[str] = Field(None, description="Player headshot URL")
    action_shot_url: Optional[str] = Field(None, description="Action shot URL")
    nhl_profile_url: Optional[str] = Field(None, description="NHL.com profile URL")


class BasicStats(BaseModel):
    """Basic hockey statistics."""
    
    games_played: int = Field(0, description="Games played")
    goals: int = Field(0, description="Goals scored")
    assists: int = Field(0, description="Assists")
    points: int = Field(0, description="Total points")
    plus_minus: int = Field(0, description="Plus/minus rating")
    penalty_minutes: int = Field(0, description="Penalty minutes")
    shots: int = Field(0, description="Shots on goal")
    shooting_percentage: float = Field(0.0, description="Shooting percentage")
    time_on_ice: str = Field("0:00", description="Average time on ice")
    power_play_goals: int = Field(0, description="Power play goals")
    power_play_assists: int = Field(0, description="Power play assists")
    short_handed_goals: int = Field(0, description="Short handed goals")
    short_handed_assists: int = Field(0, description="Short handed assists")
    game_winning_goals: int = Field(0, description="Game winning goals")
    overtime_goals: int = Field(0, description="Overtime goals")
    hits: int = Field(0, description="Hits")
    blocked_shots: int = Field(0, description="Blocked shots")
    faceoff_wins: int = Field(0, description="Faceoff wins")
    faceoff_taken: int = Field(0, description="Faceoffs taken")
    
    @property
    def faceoff_percentage(self) -> float:
        """Calculate faceoff win percentage."""
        return (self.faceoff_wins / self.faceoff_taken * 100) if self.faceoff_taken > 0 else 0.0


class GoalieStats(BaseModel):
    """Goaltender-specific statistics."""
    
    games_played: int = Field(0, description="Games played")
    games_started: int = Field(0, description="Games started")
    wins: int = Field(0, description="Wins")
    losses: int = Field(0, description="Losses")
    overtime_losses: int = Field(0, description="Overtime losses")
    saves: int = Field(0, description="Saves made")
    shots_against: int = Field(0, description="Shots faced")
    goals_against: int = Field(0, description="Goals allowed")
    goals_against_average: float = Field(0.0, description="Goals against average")
    save_percentage: float = Field(0.0, description="Save percentage")
    shutouts: int = Field(0, description="Shutouts")
    time_on_ice: str = Field("0:00", description="Total time on ice")
    penalty_minutes: int = Field(0, description="Penalty minutes")
    
    # Advanced goalie stats
    quality_starts: int = Field(0, description="Quality starts")
    really_bad_starts: int = Field(0, description="Really bad starts")
    goals_saved_above_expected: float = Field(0.0, description="Goals saved above expected")


class AdvancedStats(BaseModel):
    """Advanced hockey analytics."""
    
    # Possession metrics
    corsi_for: int = Field(0, description="Corsi for")
    corsi_against: int = Field(0, description="Corsi against")
    corsi_for_percentage: float = Field(0.0, description="Corsi for percentage")
    fenwick_for: int = Field(0, description="Fenwick for")
    fenwick_against: int = Field(0, description="Fenwick against")
    fenwick_for_percentage: float = Field(0.0, description="Fenwick for percentage")
    
    # Expected goals
    expected_goals_for: float = Field(0.0, description="Expected goals for")
    expected_goals_against: float = Field(0.0, description="Expected goals against")
    expected_goals_for_percentage: float = Field(0.0, description="xGF%")
    
    # PDO and luck metrics
    pdo: float = Field(100.0, description="PDO (shooting% + save%)")
    shooting_percentage_on_ice: float = Field(0.0, description="On-ice shooting%")
    save_percentage_on_ice: float = Field(0.0, description="On-ice save%")
    
    # Zone entries and exits
    zone_entries: int = Field(0, description="Zone entries")
    zone_exits: int = Field(0, description="Zone exits")
    controlled_zone_entries: int = Field(0, description="Controlled zone entries")
    controlled_zone_exits: int = Field(0, description="Controlled zone exits")
    
    # Danger zones
    high_danger_chances_for: int = Field(0, description="High danger chances for")
    high_danger_chances_against: int = Field(0, description="High danger chances against")
    high_danger_goals_for: int = Field(0, description="High danger goals for")
    high_danger_goals_against: int = Field(0, description="High danger goals against")


class PlayerStatsResponse(BaseModel):
    """Comprehensive player statistics response."""
    
    player_id: int = Field(..., description="Player ID")
    season: Optional[str] = Field(None, description="Season (YYYYYYYY format)")
    stat_type: str = Field("regular", description="Type of statistics")
    
    # Different stat sets based on position
    basic_stats: Optional[BasicStats] = Field(None, description="Basic skater stats")
    goalie_stats: Optional[GoalieStats] = Field(None, description="Goaltender stats")
    advanced_stats: Optional[AdvancedStats] = Field(None, description="Advanced analytics")
    
    # Metadata
    games_played: int = Field(0, description="Total games played")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    @validator("basic_stats", "goalie_stats", pre=True, always=True)
    def at_least_one_stat_set(cls, v, values):
        """Ensure at least one set of stats is provided."""
        if not v and not values.get("goalie_stats") and not values.get("basic_stats"):
            raise ValueError("At least one stat set must be provided")
        return v


class FatigueMetrics(BaseModel):
    """Fatigue analysis metrics."""
    
    fatigue_index: float = Field(..., description="Overall fatigue index (0-100)")
    
    # Contributing factors
    games_in_window: int = Field(0, description="Games played in analysis window")
    minutes_played: float = Field(0.0, description="Total minutes in window")
    travel_distance: float = Field(0.0, description="Travel distance (miles)")
    timezone_changes: int = Field(0, description="Timezone changes")
    back_to_back_games: int = Field(0, description="Back-to-back games")
    days_since_rest: int = Field(0, description="Days since last rest day")
    
    # Performance impact
    performance_decline: float = Field(0.0, description="Performance decline %")
    predicted_impact: float = Field(0.0, description="Predicted performance impact")
    
    # Risk assessment
    injury_risk: str = Field("low", description="Injury risk level")
    recommended_action: str = Field("continue", description="Recommended action")


class PlayerFatigueResponse(BaseModel):
    """Player fatigue analysis response."""
    
    player_id: int = Field(..., description="Player ID")
    analysis_date: date = Field(..., description="Date of analysis")
    window_days: int = Field(10, description="Analysis window in days")
    
    fatigue_metrics: FatigueMetrics = Field(..., description="Fatigue analysis")
    
    # Historical comparison
    season_average_fatigue: float = Field(0.0, description="Season average fatigue")
    career_average_fatigue: float = Field(0.0, description="Career average fatigue")
    peer_average_fatigue: float = Field(0.0, description="Position peer average")
    
    # Trends
    fatigue_trend: str = Field("stable", description="Fatigue trend direction")
    trend_confidence: float = Field(0.0, description="Trend confidence level")
    
    updated_at: datetime = Field(..., description="Analysis timestamp")


class PlayerComparisonMetric(BaseModel):
    """Single metric comparison between players."""
    
    metric_name: str = Field(..., description="Metric name")
    metric_type: str = Field(..., description="Metric category")
    values: Dict[int, float] = Field(..., description="Player ID to value mapping")
    league_average: float = Field(0.0, description="League average for metric")
    position_average: float = Field(0.0, description="Position average for metric")


class PlayerComparisonResponse(BaseModel):
    """Multi-player comparison response."""
    
    player_ids: List[int] = Field(..., description="Compared player IDs")
    season: Optional[str] = Field(None, description="Comparison season")
    
    # Player info for context
    players: Dict[int, PlayerBasicInfo] = Field(..., description="Player basic info")
    
    # Comparison metrics
    metrics: List[PlayerComparisonMetric] = Field(..., description="Comparison metrics")
    
    # Analysis
    similar_pairs: List[tuple[int, int]] = Field([], description="Similar player pairs")
    standout_players: Dict[str, int] = Field({}, description="Category leaders")
    
    generated_at: datetime = Field(..., description="Comparison timestamp")