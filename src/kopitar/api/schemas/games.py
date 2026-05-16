"""
Game API Schemas

Pydantic models for game-related requests and responses.
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime, date
from pydantic import BaseModel, Field, validator
from enum import Enum

from .common import PaginationParams


class GameState(str, Enum):
    """Game state enumeration."""
    SCHEDULED = "scheduled"
    PREGAME = "pregame"
    LIVE = "live"
    INTERMISSION = "intermission"
    FINAL = "final"
    POSTPONED = "postponed"
    CANCELLED = "cancelled"


class GameType(str, Enum):
    """Game type enumeration."""
    PRESEASON = "PR"
    REGULAR = "R"
    PLAYOFF = "P"
    ALL_STAR = "A"


class Period(BaseModel):
    """Period information."""
    
    period_number: int = Field(..., description="Period number")
    period_type: str = Field(..., description="Period type (REGULAR, OVERTIME, SHOOTOUT)")
    start_time: Optional[datetime] = Field(None, description="Period start time")
    end_time: Optional[datetime] = Field(None, description="Period end time")
    
    # Goals in this period
    home_goals: int = Field(0, description="Home team goals in period")
    away_goals: int = Field(0, description="Away team goals in period")
    
    # Shots in this period
    home_shots: int = Field(0, description="Home team shots in period")
    away_shots: int = Field(0, description="Away team shots in period")


class GameTeamInfo(BaseModel):
    """Team information within a game context."""
    
    team_id: int = Field(..., description="Team ID")
    team_name: str = Field(..., description="Team name")
    abbreviation: str = Field(..., description="Team abbreviation")
    
    # Score
    score: int = Field(0, description="Team score")
    
    # Shots
    shots: int = Field(0, description="Shots on goal")
    
    # Team stats for the game
    hits: int = Field(0, description="Hits")
    blocked_shots: int = Field(0, description="Blocked shots")
    takeaways: int = Field(0, description="Takeaways")
    giveaways: int = Field(0, description="Giveaways")
    penalty_minutes: int = Field(0, description="Penalty minutes")
    power_play_opportunities: int = Field(0, description="Power play opportunities")
    power_play_goals: int = Field(0, description="Power play goals")
    faceoff_wins: int = Field(0, description="Faceoff wins")
    faceoff_taken: int = Field(0, description="Faceoffs taken")
    
    @property
    def faceoff_percentage(self) -> float:
        """Calculate faceoff win percentage."""
        return (self.faceoff_wins / self.faceoff_taken * 100) if self.faceoff_taken > 0 else 0.0
    
    @property
    def power_play_percentage(self) -> float:
        """Calculate power play percentage for this game."""
        return (self.power_play_goals / self.power_play_opportunities * 100) if self.power_play_opportunities > 0 else 0.0


class GamePlayer(BaseModel):
    """Player information within a game context."""
    
    player_id: int = Field(..., description="Player ID")
    full_name: str = Field(..., description="Player full name")
    jersey_number: Optional[str] = Field(None, description="Jersey number")
    position: str = Field(..., description="Position")
    
    # Playing status
    starting: bool = Field(False, description="Was starting player")
    played: bool = Field(True, description="Did player play in game")
    time_on_ice: str = Field("0:00", description="Time on ice")
    
    # Basic stats
    goals: int = Field(0, description="Goals scored")
    assists: int = Field(0, description="Assists")
    points: int = Field(0, description="Total points")
    plus_minus: int = Field(0, description="Plus/minus rating")
    penalty_minutes: int = Field(0, description="Penalty minutes")
    shots: int = Field(0, description="Shots on goal")
    hits: int = Field(0, description="Hits")
    blocked_shots: int = Field(0, description="Blocked shots")
    
    # Faceoffs (for forwards)
    faceoff_wins: int = Field(0, description="Faceoff wins")
    faceoff_taken: int = Field(0, description="Faceoffs taken")
    
    # Special teams
    power_play_goals: int = Field(0, description="Power play goals")
    power_play_assists: int = Field(0, description="Power play assists")
    short_handed_goals: int = Field(0, description="Short handed goals")
    short_handed_assists: int = Field(0, description="Short handed assists")
    
    # Goalie-specific stats (if applicable)
    saves: Optional[int] = Field(None, description="Saves (goalies only)")
    shots_against: Optional[int] = Field(None, description="Shots against (goalies only)")
    goals_against: Optional[int] = Field(None, description="Goals against (goalies only)")
    save_percentage: Optional[float] = Field(None, description="Save percentage (goalies only)")


class GameEvent(BaseModel):
    """Individual game event."""
    
    event_id: str = Field(..., description="Unique event ID")
    event_type: str = Field(..., description="Event type (GOAL, SHOT, HIT, etc.)")
    period: int = Field(..., description="Period number")
    period_time: str = Field(..., description="Time in period")
    period_time_remaining: str = Field(..., description="Time remaining in period")
    
    # Teams and players involved
    team_id: Optional[int] = Field(None, description="Team ID for event")
    player_id: Optional[int] = Field(None, description="Primary player ID")
    player_name: Optional[str] = Field(None, description="Primary player name")
    assist1_player_id: Optional[int] = Field(None, description="First assist player ID")
    assist1_player_name: Optional[str] = Field(None, description="First assist player name")
    assist2_player_id: Optional[int] = Field(None, description="Second assist player ID")
    assist2_player_name: Optional[str] = Field(None, description="Second assist player name")
    
    # Event details
    description: str = Field(..., description="Event description")
    shot_type: Optional[str] = Field(None, description="Shot type")
    penalty_type: Optional[str] = Field(None, description="Penalty type")
    penalty_minutes: Optional[int] = Field(None, description="Penalty minutes")
    
    # Coordinates (if available)
    x_coordinate: Optional[float] = Field(None, description="X coordinate on ice")
    y_coordinate: Optional[float] = Field(None, description="Y coordinate on ice")
    
    # Score at time of event
    home_score: int = Field(0, description="Home team score after event")
    away_score: int = Field(0, description="Away team score after event")


class GameResponse(BaseModel):
    """Complete game information response."""
    
    game_id: int = Field(..., description="NHL Game ID")
    season: str = Field(..., description="Season (YYYYYYYY format)")
    game_type: GameType = Field(..., description="Game type")
    game_date: datetime = Field(..., description="Game date and time")
    
    # Game status
    game_state: GameState = Field(..., description="Current game state")
    status_detail: Optional[str] = Field(None, description="Detailed status")
    
    # Teams
    home_team: GameTeamInfo = Field(..., description="Home team information")
    away_team: GameTeamInfo = Field(..., description="Away team information")
    
    # Venue
    venue_id: Optional[int] = Field(None, description="Venue ID")
    venue_name: Optional[str] = Field(None, description="Venue name")
    
    # Timing
    period: Optional[int] = Field(None, description="Current period")
    period_ordinal: Optional[str] = Field(None, description="Period ordinal (1st, 2nd, OT)")
    period_time_remaining: Optional[str] = Field(None, description="Time remaining in period")
    intermission_time_remaining: Optional[str] = Field(None, description="Intermission time remaining")
    
    # Game context
    back_to_back_home: bool = Field(False, description="Back-to-back for home team")
    back_to_back_away: bool = Field(False, description="Back-to-back for away team")
    travel_distance_home: Optional[float] = Field(None, description="Home team travel distance")
    travel_distance_away: Optional[float] = Field(None, description="Away team travel distance")
    
    # URLs and links
    recap_url: Optional[str] = Field(None, description="Game recap URL")
    highlight_url: Optional[str] = Field(None, description="Game highlights URL")


class GameStatsResponse(BaseModel):
    """Detailed game statistics response."""
    
    game_id: int = Field(..., description="Game ID")
    game_info: GameResponse = Field(..., description="Basic game information")
    
    # Period breakdown
    periods: List[Period] = Field([], description="Period-by-period breakdown")
    
    # Player statistics
    home_skaters: List[GamePlayer] = Field([], description="Home team skaters")
    away_skaters: List[GamePlayer] = Field([], description="Away team skaters")
    home_goalies: List[GamePlayer] = Field([], description="Home team goalies")
    away_goalies: List[GamePlayer] = Field([], description="Away team goalies")
    
    # Game events (optional, can be large)
    events: Optional[List[GameEvent]] = Field(None, description="Game events")
    
    # Advanced statistics
    shot_attempts_home: Optional[int] = Field(None, description="Home shot attempts")
    shot_attempts_away: Optional[int] = Field(None, description="Away shot attempts")
    high_danger_chances_home: Optional[int] = Field(None, description="Home high danger chances")
    high_danger_chances_away: Optional[int] = Field(None, description="Away high danger chances")
    expected_goals_home: Optional[float] = Field(None, description="Home expected goals")
    expected_goals_away: Optional[float] = Field(None, description="Away expected goals")
    
    # Three stars (if game completed)
    first_star: Optional[GamePlayer] = Field(None, description="First star")
    second_star: Optional[GamePlayer] = Field(None, description="Second star")
    third_star: Optional[GamePlayer] = Field(None, description="Third star")
    
    # Officials
    referees: List[str] = Field([], description="Referees")
    linesmen: List[str] = Field([], description="Linesmen")
    
    # Metadata
    updated_at: datetime = Field(..., description="Last update timestamp")
    data_completeness: float = Field(100.0, description="Data completeness percentage")


class GameSearchRequest(BaseModel):
    """Request model for game search."""
    
    date_from: Optional[date] = Field(None, description="Start date")
    date_to: Optional[date] = Field(None, description="End date")
    team_id: Optional[int] = Field(None, description="Filter by team")
    season: Optional[str] = Field(None, description="Season filter")
    game_type: Optional[GameType] = Field(None, description="Game type filter")
    game_state: Optional[GameState] = Field(None, description="Game state filter")
    
    # Context filters
    back_to_back_only: bool = Field(False, description="Only back-to-back games")
    high_travel_only: bool = Field(False, description="Only high travel games")
    
    @validator("date_to")
    def end_date_after_start(cls, v, values):
        """Ensure end date is after start date."""
        if v and "date_from" in values and values["date_from"]:
            if v < values["date_from"]:
                raise ValueError("End date must be after start date")
        return v


class GamePrediction(BaseModel):
    """Game outcome prediction."""
    
    game_id: int = Field(..., description="Game ID")
    
    # Win probabilities
    home_win_probability: float = Field(..., description="Home team win probability")
    away_win_probability: float = Field(..., description="Away team win probability")
    overtime_probability: float = Field(..., description="Overtime probability")
    
    # Score predictions
    predicted_home_score: float = Field(..., description="Predicted home score")
    predicted_away_score: float = Field(..., description="Predicted away score")
    predicted_total_goals: float = Field(..., description="Predicted total goals")
    
    # Key factors
    fatigue_factor_home: float = Field(0.0, description="Home team fatigue factor")
    fatigue_factor_away: float = Field(0.0, description="Away team fatigue factor")
    travel_factor_home: float = Field(0.0, description="Home team travel factor")
    travel_factor_away: float = Field(0.0, description="Away team travel factor")
    
    # Model info
    model_confidence: float = Field(..., description="Prediction confidence")
    model_version: str = Field(..., description="Model version used")
    
    # Generated
    generated_at: datetime = Field(..., description="Prediction timestamp")


class GameAnalysis(BaseModel):
    """Post-game analysis."""
    
    game_id: int = Field(..., description="Game ID")
    
    # Performance analysis
    home_team_performance: Dict[str, float] = Field({}, description="Home team performance metrics")
    away_team_performance: Dict[str, float] = Field({}, description="Away team performance metrics")
    
    # Key moments
    turning_points: List[Dict[str, Any]] = Field([], description="Key turning points")
    momentum_swings: List[Dict[str, Any]] = Field([], description="Momentum changes")
    
    # Player impact
    game_changers: List[int] = Field([], description="Player IDs with high impact")
    underperformers: List[int] = Field([], description="Player IDs who underperformed")
    
    # Fatigue impact assessment
    fatigue_impact_observed: bool = Field(False, description="Was fatigue impact observed")
    fatigue_affected_players: List[int] = Field([], description="Players affected by fatigue")
    
    # Context
    upset_factor: Optional[float] = Field(None, description="Upset factor (if upset occurred)")
    competitive_balance: float = Field(0.0, description="How competitive the game was")
    
    # Analysis metadata
    analysis_confidence: float = Field(..., description="Analysis confidence level")
    generated_at: datetime = Field(..., description="Analysis timestamp")