"""
Team API Schemas

Pydantic models for team-related requests and responses.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel, Field, validator

from .common import PaginationParams


class VenueInfo(BaseModel):
    """Arena/venue information."""
    
    id: int = Field(..., description="Venue ID")
    name: str = Field(..., description="Arena name")
    city: str = Field(..., description="City")
    timezone_id: str = Field(..., description="Timezone identifier")
    timezone_offset: int = Field(..., description="UTC offset in hours")
    
    # Coordinates for travel calculations
    latitude: Optional[float] = Field(None, description="Latitude")
    longitude: Optional[float] = Field(None, description="Longitude")
    
    # Arena details
    capacity: Optional[int] = Field(None, description="Seating capacity")
    opened: Optional[int] = Field(None, description="Year opened")
    surface: Optional[str] = Field(None, description="Playing surface")


class DivisionInfo(BaseModel):
    """Division information."""
    
    id: int = Field(..., description="Division ID")
    name: str = Field(..., description="Division name")
    name_short: str = Field(..., description="Short division name")
    abbreviation: str = Field(..., description="Division abbreviation")
    active: bool = Field(True, description="Is division active")


class ConferenceInfo(BaseModel):
    """Conference information."""
    
    id: int = Field(..., description="Conference ID")
    name: str = Field(..., description="Conference name")
    abbreviation: str = Field(..., description="Conference abbreviation")
    short_name: str = Field(..., description="Short conference name")
    active: bool = Field(True, description="Is conference active")


class TeamResponse(BaseModel):
    """Complete team information response."""
    
    id: int = Field(..., description="NHL Team ID")
    name: str = Field(..., description="Full team name")
    location_name: str = Field(..., description="Team location")
    team_name: str = Field(..., description="Team name")
    abbreviation: str = Field(..., description="Team abbreviation")
    tricode: str = Field(..., description="Three-letter team code")
    
    # Organizational info
    division: DivisionInfo = Field(..., description="Division information")
    conference: ConferenceInfo = Field(..., description="Conference information")
    franchise: Optional[Dict[str, Any]] = Field(None, description="Franchise information")
    
    # Arena
    venue: VenueInfo = Field(..., description="Home venue information")
    
    # Team colors and branding
    official_site_url: Optional[str] = Field(None, description="Official website")
    primary_color: Optional[str] = Field(None, description="Primary team color (hex)")
    secondary_color: Optional[str] = Field(None, description="Secondary team color (hex)")
    
    # Status
    active: bool = Field(True, description="Is team active")
    first_year_of_play: Optional[str] = Field(None, description="First NHL season")
    
    # Social media and links
    twitter_hashtag: Optional[str] = Field(None, description="Official Twitter hashtag")
    logo_url: Optional[str] = Field(None, description="Team logo URL")


class TeamBasicStats(BaseModel):
    """Basic team statistics."""
    
    # Record
    wins: int = Field(0, description="Wins")
    losses: int = Field(0, description="Losses")
    overtime_losses: int = Field(0, description="Overtime losses")
    points: int = Field(0, description="Total points")
    points_percentage: float = Field(0.0, description="Points percentage")
    
    # Standings
    division_rank: Optional[int] = Field(None, description="Division rank")
    conference_rank: Optional[int] = Field(None, description="Conference rank")
    league_rank: Optional[int] = Field(None, description="League rank")
    wildcard_rank: Optional[int] = Field(None, description="Wildcard rank")
    
    # Games
    games_played: int = Field(0, description="Games played")
    games_remaining: int = Field(0, description="Games remaining")
    
    # Goal differential
    goals_for: int = Field(0, description="Goals for")
    goals_against: int = Field(0, description="Goals against")
    goal_differential: int = Field(0, description="Goal differential")
    
    # Streaks
    current_streak: Optional[str] = Field(None, description="Current streak (e.g., 'W3')")
    longest_win_streak: int = Field(0, description="Longest win streak this season")
    longest_lose_streak: int = Field(0, description="Longest losing streak this season")
    
    # Home/Road splits
    home_record: Optional[str] = Field(None, description="Home record (W-L-OTL)")
    road_record: Optional[str] = Field(None, description="Road record (W-L-OTL)")
    
    @property
    def win_percentage(self) -> float:
        """Calculate win percentage."""
        total_games = self.wins + self.losses + self.overtime_losses
        return (self.wins / total_games) if total_games > 0 else 0.0


class TeamAdvancedStats(BaseModel):
    """Advanced team analytics."""
    
    # Possession metrics
    corsi_for_percentage: float = Field(0.0, description="Corsi for percentage")
    fenwick_for_percentage: float = Field(0.0, description="Fenwick for percentage")
    shots_for_percentage: float = Field(0.0, description="Shots for percentage")
    
    # Expected goals
    expected_goals_for: float = Field(0.0, description="Expected goals for")
    expected_goals_against: float = Field(0.0, description="Expected goals against")
    expected_goals_for_percentage: float = Field(0.0, description="xGF%")
    
    # Efficiency
    shooting_percentage: float = Field(0.0, description="Team shooting percentage")
    save_percentage: float = Field(0.0, description="Team save percentage")
    pdo: float = Field(100.0, description="PDO (shooting% + save%)")
    
    # Special teams
    power_play_percentage: float = Field(0.0, description="Power play percentage")
    penalty_kill_percentage: float = Field(0.0, description="Penalty kill percentage")
    power_play_opportunities: int = Field(0, description="Power play opportunities")
    times_short_handed: int = Field(0, description="Times short handed")
    
    # Discipline
    penalties_taken: int = Field(0, description="Penalties taken")
    penalty_minutes: int = Field(0, description="Penalty minutes")
    penalties_drawn: int = Field(0, description="Penalties drawn")
    
    # Zone performance
    offensive_zone_start_percentage: float = Field(0.0, description="Offensive zone start %")
    high_danger_chances_for: int = Field(0, description="High danger chances for")
    high_danger_chances_against: int = Field(0, description="High danger chances against")
    
    # Close game performance
    one_goal_record: Optional[str] = Field(None, description="One-goal game record")
    lead_after_1st_record: Optional[str] = Field(None, description="Lead after 1st record")
    lead_after_2nd_record: Optional[str] = Field(None, description="Lead after 2nd record")
    trail_after_1st_record: Optional[str] = Field(None, description="Trail after 1st record")
    trail_after_2nd_record: Optional[str] = Field(None, description="Trail after 2nd record")


class TeamFatigueMetrics(BaseModel):
    """Team-level fatigue analysis."""
    
    average_fatigue_index: float = Field(0.0, description="Team average fatigue index")
    high_fatigue_players: int = Field(0, description="Players with high fatigue")
    
    # Schedule factors
    back_to_back_games: int = Field(0, description="Back-to-back games played")
    three_in_four_games: int = Field(0, description="Three-games-in-four-nights")
    total_travel_miles: float = Field(0.0, description="Total travel distance")
    timezone_changes: int = Field(0, description="Total timezone changes")
    
    # Performance impact
    fatigue_performance_correlation: float = Field(0.0, description="Fatigue-performance correlation")
    predicted_fatigue_impact: float = Field(0.0, description="Predicted performance impact")
    
    # Risk assessment
    injury_risk_level: str = Field("low", description="Team injury risk level")
    recommended_rest_players: List[int] = Field([], description="Player IDs needing rest")


class TeamRoster(BaseModel):
    """Team roster information."""
    
    forwards: List[Dict[str, Any]] = Field([], description="Forward players")
    defensemen: List[Dict[str, Any]] = Field([], description="Defensemen")
    goalies: List[Dict[str, Any]] = Field([], description="Goaltenders")
    
    # Counts
    total_players: int = Field(0, description="Total roster size")
    injured_players: int = Field(0, description="Players on injured reserve")
    salary_cap_space: Optional[float] = Field(None, description="Salary cap space")


class TeamStatsResponse(BaseModel):
    """Comprehensive team statistics response."""
    
    team_id: int = Field(..., description="Team ID")
    season: Optional[str] = Field(None, description="Season (YYYYYYYY format)")
    stat_type: str = Field("regular", description="Type of statistics")
    
    # Statistics
    basic_stats: TeamBasicStats = Field(..., description="Basic team statistics")
    advanced_stats: Optional[TeamAdvancedStats] = Field(None, description="Advanced analytics")
    fatigue_metrics: Optional[TeamFatigueMetrics] = Field(None, description="Fatigue analysis")
    
    # Roster
    roster_summary: Optional[TeamRoster] = Field(None, description="Roster information")
    
    # Recent performance
    last_10_games: Optional[str] = Field(None, description="Record in last 10 games")
    trend_direction: Optional[str] = Field(None, description="Performance trend")
    
    # Metadata
    updated_at: datetime = Field(..., description="Last update timestamp")
    data_completeness: float = Field(100.0, description="Data completeness percentage")


class TeamScheduleGame(BaseModel):
    """Single game in team schedule."""
    
    game_id: int = Field(..., description="Game ID")
    game_date: datetime = Field(..., description="Game date and time")
    home_away: str = Field(..., description="Home or Away")
    opponent_id: int = Field(..., description="Opponent team ID")
    opponent_name: str = Field(..., description="Opponent team name")
    
    # Game status
    game_state: str = Field(..., description="Game state (scheduled, live, final)")
    period: Optional[int] = Field(None, description="Current/final period")
    time_remaining: Optional[str] = Field(None, description="Time remaining")
    
    # Scores (if game completed/in progress)
    team_score: Optional[int] = Field(None, description="Team score")
    opponent_score: Optional[int] = Field(None, description="Opponent score")
    
    # Context
    back_to_back: bool = Field(False, description="Is back-to-back game")
    travel_distance: Optional[float] = Field(None, description="Travel distance to game")
    timezone_change: Optional[int] = Field(None, description="Timezone change")
    rest_days: int = Field(0, description="Rest days before game")


class TeamScheduleResponse(BaseModel):
    """Team schedule response."""
    
    team_id: int = Field(..., description="Team ID")
    season: str = Field(..., description="Season")
    
    games: List[TeamScheduleGame] = Field(..., description="Scheduled games")
    
    # Schedule analysis
    total_games: int = Field(82, description="Total games in season")
    games_played: int = Field(0, description="Games played")
    games_remaining: int = Field(82, description="Games remaining")
    
    back_to_back_count: int = Field(0, description="Total back-to-back games")
    three_in_four_count: int = Field(0, description="Three-in-four scenarios")
    total_travel_miles: float = Field(0.0, description="Total season travel")
    
    # Upcoming schedule difficulty
    next_10_games_difficulty: Optional[float] = Field(None, description="Upcoming schedule difficulty")
    strength_of_schedule: Optional[float] = Field(None, description="Overall schedule strength")
    
    updated_at: datetime = Field(..., description="Last update timestamp")