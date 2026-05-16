"""
Player Statistics Database Models

Models for tracking individual player game and advanced statistics.
"""

from sqlalchemy import (
    Column, Integer, String, Boolean, Float, ForeignKey, DateTime, Text, Enum
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
import enum

from .base import BaseModel, AuditMixin


class PlayerGameStats(BaseModel, AuditMixin):
    """
    Individual player statistics for a specific game.
    """
    
    __tablename__ = 'player_game_stats'
    
    # Relationships
    player_id = Column(Integer, ForeignKey('players.id'), nullable=False, index=True)
    player = relationship("Player", back_populates="game_stats")
    
    game_id = Column(Integer, ForeignKey('games.id'), nullable=False, index=True)
    game = relationship("Game", back_populates="player_stats")
    
    team_id = Column(Integer, ForeignKey('teams.id'), nullable=False, index=True)
    team = relationship("Team")
    
    # Game Information
    home_away = Column(String(4), nullable=False)  # "home" or "away"
    jersey_number = Column(String(3), nullable=True)
    position = Column(String(10), nullable=False)  # Position played in this game
    
    # Playing Time
    time_on_ice = Column(String(10), nullable=True)  # "20:15"
    time_on_ice_seconds = Column(Integer, nullable=False, default=0)
    shifts = Column(Integer, nullable=False, default=0)
    
    # Basic Statistics
    goals = Column(Integer, nullable=False, default=0)
    assists = Column(Integer, nullable=False, default=0)
    points = Column(Integer, nullable=False, default=0)
    plus_minus = Column(Integer, nullable=False, default=0)
    
    # Shooting
    shots = Column(Integer, nullable=False, default=0)
    shooting_percentage = Column(Float, nullable=False, default=0.0)
    
    # Special Teams
    power_play_goals = Column(Integer, nullable=False, default=0)
    power_play_assists = Column(Integer, nullable=False, default=0)
    power_play_points = Column(Integer, nullable=False, default=0)
    power_play_time_on_ice = Column(Integer, nullable=False, default=0)  # seconds
    
    short_handed_goals = Column(Integer, nullable=False, default=0)
    short_handed_assists = Column(Integer, nullable=False, default=0)
    short_handed_points = Column(Integer, nullable=False, default=0)
    short_handed_time_on_ice = Column(Integer, nullable=False, default=0)  # seconds
    
    # Even Strength
    even_strength_goals = Column(Integer, nullable=False, default=0)
    even_strength_assists = Column(Integer, nullable=False, default=0)
    even_strength_points = Column(Integer, nullable=False, default=0)
    even_strength_time_on_ice = Column(Integer, nullable=False, default=0)  # seconds
    
    # Physical Play
    hits = Column(Integer, nullable=False, default=0)
    blocked_shots = Column(Integer, nullable=False, default=0)
    penalty_minutes = Column(Integer, nullable=False, default=0)
    
    # Faceoffs (for centers)
    faceoff_wins = Column(Integer, nullable=False, default=0)
    faceoff_losses = Column(Integer, nullable=False, default=0)
    faceoff_percentage = Column(Float, nullable=False, default=0.0)
    
    # Giveaways and Takeaways
    giveaways = Column(Integer, nullable=False, default=0)
    takeaways = Column(Integer, nullable=False, default=0)
    
    # Special Situations
    game_winning_goals = Column(Integer, nullable=False, default=0)
    game_tying_goals = Column(Integer, nullable=False, default=0)
    overtime_goals = Column(Integer, nullable=False, default=0)
    shootout_goals = Column(Integer, nullable=False, default=0)
    shootout_attempts = Column(Integer, nullable=False, default=0)
    
    # Penalties
    penalties = Column(Integer, nullable=False, default=0)
    major_penalties = Column(Integer, nullable=False, default=0)
    misconduct_penalties = Column(Integer, nullable=False, default=0)
    
    # Game Status
    scratched = Column(Boolean, nullable=False, default=False)
    injured = Column(Boolean, nullable=False, default=False)
    
    def __repr__(self):
        return f"<PlayerGameStats(player_id={self.player_id}, game_id={self.game_id})>"
    
    @property
    def points_per_60(self):
        """Calculate points per 60 minutes."""
        if self.time_on_ice_seconds == 0:
            return 0.0
        return round((self.points * 3600) / self.time_on_ice_seconds, 2)
    
    @property
    def goals_per_60(self):
        """Calculate goals per 60 minutes."""
        if self.time_on_ice_seconds == 0:
            return 0.0
        return round((self.goals * 3600) / self.time_on_ice_seconds, 2)
    
    @property
    def shots_per_60(self):
        """Calculate shots per 60 minutes."""
        if self.time_on_ice_seconds == 0:
            return 0.0
        return round((self.shots * 3600) / self.time_on_ice_seconds, 2)


class GoalieGameStats(BaseModel, AuditMixin):
    """
    Goaltender-specific statistics for a game.
    """
    
    __tablename__ = 'goalie_game_stats'
    
    # Relationships
    player_id = Column(Integer, ForeignKey('players.id'), nullable=False, index=True)
    player = relationship("Player", back_populates="goalie_stats")
    
    game_id = Column(Integer, ForeignKey('games.id'), nullable=False, index=True)
    game = relationship("Game", back_populates="goalie_stats")
    
    team_id = Column(Integer, ForeignKey('teams.id'), nullable=False, index=True)
    team = relationship("Team")
    
    # Game Information
    home_away = Column(String(4), nullable=False)  # "home" or "away"
    jersey_number = Column(String(3), nullable=True)
    starter = Column(Boolean, nullable=False, default=True)
    
    # Playing Time
    time_on_ice = Column(String(10), nullable=True)  # "60:00"
    time_on_ice_seconds = Column(Integer, nullable=False, default=0)
    
    # Basic Goalie Statistics
    decision = Column(String(10), nullable=True)  # "W", "L", "OT", "SO", None
    shots_against = Column(Integer, nullable=False, default=0)
    saves = Column(Integer, nullable=False, default=0)
    goals_against = Column(Integer, nullable=False, default=0)
    
    # Calculated Statistics
    save_percentage = Column(Float, nullable=False, default=0.0)
    goals_against_average = Column(Float, nullable=False, default=0.0)
    
    # Shot Quality
    low_danger_shots_against = Column(Integer, nullable=True)
    low_danger_saves = Column(Integer, nullable=True)
    medium_danger_shots_against = Column(Integer, nullable=True)
    medium_danger_saves = Column(Integer, nullable=True)
    high_danger_shots_against = Column(Integer, nullable=True)
    high_danger_saves = Column(Integer, nullable=True)
    
    # Special Situations
    power_play_shots_against = Column(Integer, nullable=False, default=0)
    power_play_saves = Column(Integer, nullable=False, default=0)
    power_play_goals_against = Column(Integer, nullable=False, default=0)
    
    short_handed_shots_against = Column(Integer, nullable=False, default=0)
    short_handed_saves = Column(Integer, nullable=False, default=0)
    short_handed_goals_against = Column(Integer, nullable=False, default=0)
    
    even_strength_shots_against = Column(Integer, nullable=False, default=0)
    even_strength_saves = Column(Integer, nullable=False, default=0)
    even_strength_goals_against = Column(Integer, nullable=False, default=0)
    
    # Advanced Metrics
    expected_goals_against = Column(Float, nullable=True)
    goals_saved_above_expected = Column(Float, nullable=True)  # GSAx
    
    # Penalty Shot and Shootout
    penalty_shots_faced = Column(Integer, nullable=False, default=0)
    penalty_shots_saved = Column(Integer, nullable=False, default=0)
    shootout_shots_faced = Column(Integer, nullable=False, default=0)
    shootout_saves = Column(Integer, nullable=False, default=0)
    
    # Rebound Control
    rebounds_allowed = Column(Integer, nullable=True)
    rebound_goals_against = Column(Integer, nullable=True)
    
    # Other
    assists = Column(Integer, nullable=False, default=0)
    penalty_minutes = Column(Integer, nullable=False, default=0)
    pulled = Column(Boolean, nullable=False, default=False)
    pulled_time = Column(Integer, nullable=True)  # Time when pulled (seconds from start)
    
    # Quality Metrics
    quality_start = Column(Boolean, nullable=True)  # Save % >= 0.885 or <= 2 GA if < 20 shots
    really_bad_start = Column(Boolean, nullable=True)  # Save % < 0.850
    
    def __repr__(self):
        return f"<GoalieGameStats(player_id={self.player_id}, game_id={self.game_id})>"
    
    @property
    def shutout(self):
        """Check if this was a shutout."""
        return self.goals_against == 0 and self.time_on_ice_seconds >= 3600  # Full game
    
    @property
    def high_danger_save_percentage(self):
        """Calculate high danger save percentage."""
        if not self.high_danger_shots_against or self.high_danger_shots_against == 0:
            return None
        return round((self.high_danger_saves / self.high_danger_shots_against) * 100, 1)
    
    @property
    def power_play_save_percentage(self):
        """Calculate power play save percentage."""
        if self.power_play_shots_against == 0:
            return None
        return round((self.power_play_saves / self.power_play_shots_against) * 100, 1)
    
    @property
    def even_strength_save_percentage(self):
        """Calculate even strength save percentage."""
        if self.even_strength_shots_against == 0:
            return None
        return round((self.even_strength_saves / self.even_strength_shots_against) * 100, 1)


class PlayerAdvancedStats(BaseModel, AuditMixin):
    """
    Advanced analytics for player performance in a game.
    """
    
    __tablename__ = 'player_advanced_stats'
    
    # Relationships
    player_id = Column(Integer, ForeignKey('players.id'), nullable=False, index=True)
    player = relationship("Player", back_populates="advanced_stats")
    
    game_id = Column(Integer, ForeignKey('games.id'), nullable=False, index=True)
    game = relationship("Game")
    
    team_id = Column(Integer, ForeignKey('teams.id'), nullable=False, index=True)
    team = relationship("Team")
    
    # Corsi (Shot Attempts)
    corsi_for = Column(Integer, nullable=True)
    corsi_against = Column(Integer, nullable=True)
    corsi_percentage = Column(Float, nullable=True)
    
    # Fenwick (Unblocked Shot Attempts)
    fenwick_for = Column(Integer, nullable=True)
    fenwick_against = Column(Integer, nullable=True)
    fenwick_percentage = Column(Float, nullable=True)
    
    # Expected Goals
    expected_goals_for = Column(Float, nullable=True)
    expected_goals_against = Column(Float, nullable=True)
    expected_goals_percentage = Column(Float, nullable=True)
    
    # Individual Expected Goals
    individual_expected_goals = Column(Float, nullable=True)
    individual_corsi_for = Column(Integer, nullable=True)
    individual_fenwick_for = Column(Integer, nullable=True)
    
    # Zone Starts
    offensive_zone_starts = Column(Integer, nullable=True)
    defensive_zone_starts = Column(Integer, nullable=True)
    neutral_zone_starts = Column(Integer, nullable=True)
    on_the_fly_starts = Column(Integer, nullable=True)
    
    # PDO Components
    on_ice_shooting_percentage = Column(Float, nullable=True)
    on_ice_save_percentage = Column(Float, nullable=True)
    pdo = Column(Float, nullable=True)
    
    # Relative Metrics (compared to team)
    relative_corsi = Column(Float, nullable=True)
    relative_fenwick = Column(Float, nullable=True)
    relative_expected_goals = Column(Float, nullable=True)
    
    # Quality of Competition
    quality_of_competition = Column(Float, nullable=True)
    quality_of_teammates = Column(Float, nullable=True)
    
    # Game Score (all-in-one metric)
    game_score = Column(Float, nullable=True)
    
    def __repr__(self):
        return f"<PlayerAdvancedStats(player_id={self.player_id}, game_id={self.game_id})>"
    
    @property
    def shot_attempt_differential(self):
        """Calculate shot attempt differential."""
        if self.corsi_for is None or self.corsi_against is None:
            return None
        return self.corsi_for - self.corsi_against
    
    @property
    def expected_goal_differential(self):
        """Calculate expected goal differential."""
        if self.expected_goals_for is None or self.expected_goals_against is None:
            return None
        return round(self.expected_goals_for - self.expected_goals_against, 2)
    
    @property
    def zone_start_percentage(self):
        """Calculate offensive zone start percentage."""
        if not self.offensive_zone_starts or not self.defensive_zone_starts:
            return None
        
        total_zone_starts = self.offensive_zone_starts + self.defensive_zone_starts
        if total_zone_starts == 0:
            return None
        
        return round((self.offensive_zone_starts / total_zone_starts) * 100, 1)