"""
Game Database Models

Models for NHL games, periods, and team game statistics.
"""

from sqlalchemy import (
    Column, Integer, String, Boolean, Float, ForeignKey, DateTime, Text, Enum
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
import enum

from .base import BaseModel, AuditMixin


class GameType(enum.Enum):
    """Game type enumeration."""
    PRESEASON = "PR"
    REGULAR = "R"
    PLAYOFF = "P"
    ALL_STAR = "A"


class GameState(enum.Enum):
    """Game state enumeration."""
    PREVIEW = "Preview"
    LIVE = "Live"
    FINAL = "Final"
    POSTPONED = "Postponed"


class PeriodType(enum.Enum):
    """Period type enumeration."""
    REGULATION = "REGULAR"
    OVERTIME = "OVERTIME"
    SHOOTOUT = "SHOOTOUT"


class Game(BaseModel, AuditMixin):
    """
    NHL Game model with comprehensive game information.
    """
    
    __tablename__ = 'games'
    
    # NHL Game ID
    nhl_id = Column(Integer, unique=True, nullable=False, index=True)
    
    # Season and Game Information
    season = Column(String(8), nullable=False, index=True)  # "20232024"
    game_type = Column(Enum(GameType), nullable=False, index=True)
    game_number = Column(Integer, nullable=False)  # Game number in season
    
    # Teams
    home_team_id = Column(Integer, ForeignKey('teams.id'), nullable=False, index=True)
    home_team = relationship("Team", foreign_keys=[home_team_id], back_populates="home_games")
    
    away_team_id = Column(Integer, ForeignKey('teams.id'), nullable=False, index=True)
    away_team = relationship("Team", foreign_keys=[away_team_id], back_populates="away_games")
    
    # Venue
    venue_id = Column(Integer, ForeignKey('venues.id'), nullable=False)
    venue = relationship("Venue", back_populates="home_games")
    
    # Game Timing
    game_date = Column(DateTime, nullable=False, index=True)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    
    # Game Status
    game_state = Column(Enum(GameState), nullable=False, default=GameState.PREVIEW)
    current_period = Column(Integer, nullable=True)
    current_period_ordinal = Column(String(10), nullable=True)  # "1st", "2nd", "OT"
    current_period_time_remaining = Column(String(10), nullable=True)  # "15:30"
    
    # Score Information
    home_score = Column(Integer, nullable=False, default=0)
    away_score = Column(Integer, nullable=False, default=0)
    
    # Period Scores (JSON for flexibility)
    period_scores = Column(JSONB, nullable=True)  # {"1": {"home": 1, "away": 0}, ...}
    
    # Game Details
    attendance = Column(Integer, nullable=True)
    duration_minutes = Column(Integer, nullable=True)  # Total game duration
    
    # Officials
    officials = Column(JSONB, nullable=True)  # Referees and linesmen
    
    # Weather (for outdoor games)
    weather_conditions = Column(Text, nullable=True)
    temperature = Column(String(20), nullable=True)
    
    # Broadcast Information
    broadcast_info = Column(JSONB, nullable=True)
    
    # Game Notes
    notes = Column(Text, nullable=True)
    
    # Relationships
    periods = relationship("Period", back_populates="game", cascade="all, delete-orphan")
    team_stats = relationship("GameTeamStats", back_populates="game", cascade="all, delete-orphan")
    player_stats = relationship("PlayerGameStats", back_populates="game", cascade="all, delete-orphan")
    goalie_stats = relationship("GoalieGameStats", back_populates="game", cascade="all, delete-orphan")
    travel_logs = relationship("TravelLog", back_populates="game", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Game(id={self.nhl_id}, {self.away_team.tricode if self.away_team else '?'} @ {self.home_team.tricode if self.home_team else '?'})>"
    
    @property
    def is_back_to_back_home(self):
        """Check if this is a back-to-back game for home team."""
        # This would require a database query to find previous game
        return None
    
    @property
    def is_back_to_back_away(self):
        """Check if this is a back-to-back game for away team."""
        # This would require a database query to find previous game
        return None
    
    @property
    def winner(self):
        """Get the winning team."""
        if self.game_state != GameState.FINAL:
            return None
        
        if self.home_score > self.away_score:
            return self.home_team
        elif self.away_score > self.home_score:
            return self.away_team
        else:
            return None  # Tie (shouldn't happen in modern NHL)
    
    @property
    def loser(self):
        """Get the losing team."""
        if self.game_state != GameState.FINAL:
            return None
        
        if self.home_score > self.away_score:
            return self.away_team
        elif self.away_score > self.home_score:
            return self.home_team
        else:
            return None
    
    @property
    def total_goals(self):
        """Get total goals scored in the game."""
        return self.home_score + self.away_score
    
    @property
    def goal_differential(self):
        """Get goal differential (home - away)."""
        return self.home_score - self.away_score
    
    def get_team_stats(self, team_id):
        """
        Get team statistics for this game.
        
        Args:
            team_id: Team ID
            
        Returns:
            GameTeamStats: Team stats or None
        """
        return next(
            (stats for stats in self.team_stats if stats.team_id == team_id),
            None
        )


class Period(BaseModel, AuditMixin):
    """
    Game period model for tracking period-specific data.
    """
    
    __tablename__ = 'periods'
    
    # Game relationship
    game_id = Column(Integer, ForeignKey('games.id'), nullable=False, index=True)
    game = relationship("Game", back_populates="periods")
    
    # Period Information
    period_number = Column(Integer, nullable=False)
    period_type = Column(Enum(PeriodType), nullable=False)
    ordinal = Column(String(10), nullable=False)  # "1st", "2nd", "OT", "SO"
    
    # Timing
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    
    # Scores
    home_goals = Column(Integer, nullable=False, default=0)
    away_goals = Column(Integer, nullable=False, default=0)
    home_shots = Column(Integer, nullable=False, default=0)
    away_shots = Column(Integer, nullable=False, default=0)
    
    # Advanced Statistics
    home_hits = Column(Integer, nullable=False, default=0)
    away_hits = Column(Integer, nullable=False, default=0)
    home_blocks = Column(Integer, nullable=False, default=0)
    away_blocks = Column(Integer, nullable=False, default=0)
    home_giveaways = Column(Integer, nullable=False, default=0)
    away_giveaways = Column(Integer, nullable=False, default=0)
    home_takeaways = Column(Integer, nullable=False, default=0)
    away_takeaways = Column(Integer, nullable=False, default=0)
    home_faceoff_wins = Column(Integer, nullable=False, default=0)
    away_faceoff_wins = Column(Integer, nullable=False, default=0)
    
    # Power Play
    home_power_play_opportunities = Column(Integer, nullable=False, default=0)
    away_power_play_opportunities = Column(Integer, nullable=False, default=0)
    home_power_play_goals = Column(Integer, nullable=False, default=0)
    away_power_play_goals = Column(Integer, nullable=False, default=0)
    
    # Penalty Minutes
    home_penalty_minutes = Column(Integer, nullable=False, default=0)
    away_penalty_minutes = Column(Integer, nullable=False, default=0)
    
    def __repr__(self):
        return f"<Period(game_id={self.game_id}, period={self.ordinal})>"
    
    @property
    def total_shots(self):
        """Get total shots in the period."""
        return self.home_shots + self.away_shots
    
    @property
    def shot_differential(self):
        """Get shot differential (home - away)."""
        return self.home_shots - self.away_shots


class GameTeamStats(BaseModel, AuditMixin):
    """
    Team-level statistics for a specific game.
    """
    
    __tablename__ = 'game_team_stats'
    
    # Relationships
    game_id = Column(Integer, ForeignKey('games.id'), nullable=False, index=True)
    game = relationship("Game", back_populates="team_stats")
    
    team_id = Column(Integer, ForeignKey('teams.id'), nullable=False, index=True)
    team = relationship("Team", back_populates="game_team_stats")
    
    # Game Result
    home_away = Column(String(4), nullable=False)  # "home" or "away"
    won = Column(Boolean, nullable=False)
    overtime = Column(Boolean, nullable=False, default=False)
    shootout = Column(Boolean, nullable=False, default=False)
    
    # Scoring
    goals = Column(Integer, nullable=False, default=0)
    assists = Column(Integer, nullable=False, default=0)
    points = Column(Integer, nullable=False, default=0)
    
    # Shooting
    shots = Column(Integer, nullable=False, default=0)
    shooting_percentage = Column(Float, nullable=False, default=0.0)
    
    # Special Teams
    power_play_goals = Column(Integer, nullable=False, default=0)
    power_play_opportunities = Column(Integer, nullable=False, default=0)
    power_play_percentage = Column(Float, nullable=False, default=0.0)
    
    short_handed_goals = Column(Integer, nullable=False, default=0)
    penalty_kill_opportunities = Column(Integer, nullable=False, default=0)
    penalty_kill_percentage = Column(Float, nullable=False, default=0.0)
    
    # Physical Play
    hits = Column(Integer, nullable=False, default=0)
    blocked_shots = Column(Integer, nullable=False, default=0)
    penalty_minutes = Column(Integer, nullable=False, default=0)
    
    # Possession
    faceoff_wins = Column(Integer, nullable=False, default=0)
    faceoff_losses = Column(Integer, nullable=False, default=0)
    faceoff_percentage = Column(Float, nullable=False, default=0.0)
    
    giveaways = Column(Integer, nullable=False, default=0)
    takeaways = Column(Integer, nullable=False, default=0)
    
    # Advanced Statistics (if available)
    corsi_for = Column(Integer, nullable=True)
    corsi_against = Column(Integer, nullable=True)
    fenwick_for = Column(Integer, nullable=True)
    fenwick_against = Column(Integer, nullable=True)
    
    # Expected Goals (if available)
    expected_goals_for = Column(Float, nullable=True)
    expected_goals_against = Column(Float, nullable=True)
    
    # High Danger Chances
    high_danger_chances_for = Column(Integer, nullable=True)
    high_danger_chances_against = Column(Integer, nullable=True)
    
    def __repr__(self):
        return f"<GameTeamStats(game_id={self.game_id}, team_id={self.team_id})>"
    
    @property
    def corsi_percentage(self):
        """Calculate Corsi percentage."""
        if not self.corsi_for or not self.corsi_against:
            return None
        
        total_corsi = self.corsi_for + self.corsi_against
        if total_corsi == 0:
            return 0.0
        
        return round((self.corsi_for / total_corsi) * 100, 1)
    
    @property
    def fenwick_percentage(self):
        """Calculate Fenwick percentage."""
        if not self.fenwick_for or not self.fenwick_against:
            return None
        
        total_fenwick = self.fenwick_for + self.fenwick_against
        if total_fenwick == 0:
            return 0.0
        
        return round((self.fenwick_for / total_fenwick) * 100, 1)
    
    @property
    def pdo(self):
        """Calculate PDO (shooting % + save %)."""
        # This would require additional calculation based on goalie stats
        return None