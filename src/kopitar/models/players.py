"""
Player Database Models

Models for NHL players with career tracking and seasonal data.
"""

from sqlalchemy import (
    Column, Integer, String, Boolean, Float, ForeignKey, Date, Text, Enum
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import date, datetime
import enum

from .base import BaseModel, AuditMixin


class Position(enum.Enum):
    """Player position enumeration."""
    GOALIE = "G"
    DEFENSE = "D"
    LEFT_WING = "LW"
    RIGHT_WING = "RW"
    CENTER = "C"
    FORWARD = "F"  # Generic forward


class ShootsCatches(enum.Enum):
    """Shooting/catching hand enumeration."""
    LEFT = "L"
    RIGHT = "R"


class Player(BaseModel, AuditMixin):
    """
    NHL Player model with biographical and career information.
    """
    
    __tablename__ = 'players'
    
    # NHL Player ID
    nhl_id = Column(Integer, unique=True, nullable=False, index=True)
    
    # Personal Information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False, index=True)
    full_name = Column(String(200), nullable=False, index=True)
    
    # Birth Information
    birth_date = Column(Date, nullable=True)
    birth_city = Column(String(100), nullable=True)
    birth_state_province = Column(String(50), nullable=True)
    birth_country = Column(String(50), nullable=True)
    nationality = Column(String(50), nullable=True)
    
    # Physical Attributes
    height = Column(String(10), nullable=True)  # "6'2\""
    height_inches = Column(Integer, nullable=True)  # Total inches for calculations
    weight = Column(Integer, nullable=True)  # Pounds
    
    # Playing Information
    position = Column(Enum(Position), nullable=False, index=True)
    shoots_catches = Column(Enum(ShootsCatches), nullable=True)
    
    # Current Team (can change during season)
    current_team_id = Column(Integer, ForeignKey('teams.id'), nullable=True)
    current_team = relationship("Team", back_populates="players")
    
    # Career Information
    nhl_debut = Column(Date, nullable=True)
    rookie = Column(Boolean, nullable=False, default=False)
    active = Column(Boolean, nullable=False, default=True)
    
    # Leadership
    captain = Column(Boolean, nullable=False, default=False)
    alternate_captain = Column(Boolean, nullable=False, default=False)
    
    # External Data
    headshot_url = Column(String(500), nullable=True)
    action_shot_url = Column(String(500), nullable=True)
    nhl_profile_url = Column(String(500), nullable=True)
    
    # Additional Information
    draft_year = Column(Integer, nullable=True)
    draft_round = Column(Integer, nullable=True)
    draft_pick = Column(Integer, nullable=True)
    draft_team_id = Column(Integer, ForeignKey('teams.id'), nullable=True)
    
    # Relationships
    seasons = relationship("PlayerSeason", back_populates="player", cascade="all, delete-orphan")
    game_stats = relationship("PlayerGameStats", back_populates="player", cascade="all, delete-orphan")
    goalie_stats = relationship("GoalieGameStats", back_populates="player", cascade="all, delete-orphan")
    advanced_stats = relationship("PlayerAdvancedStats", back_populates="player", cascade="all, delete-orphan")
    fatigue_metrics = relationship("PlayerFatigueMetrics", back_populates="player", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="player", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Player(name='{self.full_name}', position='{self.position.value}')>"
    
    @property
    def age(self):
        """Calculate current age."""
        if not self.birth_date:
            return None
        
        today = date.today()
        return today.year - self.birth_date.year - (
            (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        )
    
    @property
    def age_group(self):
        """Get age group category for analysis."""
        age = self.age
        if not age:
            return "unknown"
        
        if age < 25:
            return "young"
        elif age < 30:
            return "prime"
        elif age < 35:
            return "veteran"
        else:
            return "elder"
    
    @property
    def is_goalie(self):
        """Check if player is a goaltender."""
        return self.position == Position.GOALIE
    
    @property
    def is_forward(self):
        """Check if player is a forward."""
        return self.position in (Position.LEFT_WING, Position.RIGHT_WING, Position.CENTER, Position.FORWARD)
    
    @property
    def is_defense(self):
        """Check if player is a defenseman."""
        return self.position == Position.DEFENSE
    
    def get_season_stats(self, season):
        """
        Get player statistics for a specific season.
        
        Args:
            season: Season string (e.g., "20232024")
            
        Returns:
            PlayerSeason: Season statistics or None
        """
        return next(
            (s for s in self.seasons if s.season == season),
            None
        )
    
    def career_games_played(self):
        """Get total career games played."""
        return sum(season.games_played for season in self.seasons)
    
    def seasons_played(self):
        """Get number of NHL seasons played."""
        return len(self.seasons)


class PlayerSeason(BaseModel, AuditMixin):
    """
    Player seasonal statistics and information.
    """
    
    __tablename__ = 'player_seasons'
    
    # Relationships
    player_id = Column(Integer, ForeignKey('players.id'), nullable=False, index=True)
    player = relationship("Player", back_populates="seasons")
    
    team_id = Column(Integer, ForeignKey('teams.id'), nullable=False)
    team = relationship("Team", back_populates="player_seasons")
    
    # Season Information
    season = Column(String(8), nullable=False, index=True)  # "20232024"
    season_type = Column(String(20), nullable=False, default="regular")  # regular, playoff
    
    # Jersey Information
    jersey_number = Column(String(3), nullable=True)
    
    # Basic Statistics
    games_played = Column(Integer, nullable=False, default=0)
    
    # Skater Statistics
    goals = Column(Integer, nullable=False, default=0)
    assists = Column(Integer, nullable=False, default=0)
    points = Column(Integer, nullable=False, default=0)
    plus_minus = Column(Integer, nullable=False, default=0)
    penalty_minutes = Column(Integer, nullable=False, default=0)
    shots = Column(Integer, nullable=False, default=0)
    shooting_percentage = Column(Float, nullable=False, default=0.0)
    
    # Time on Ice
    time_on_ice_per_game = Column(String(10), nullable=True)  # "20:15"
    time_on_ice_total_seconds = Column(Integer, nullable=False, default=0)
    
    # Special Teams
    power_play_goals = Column(Integer, nullable=False, default=0)
    power_play_assists = Column(Integer, nullable=False, default=0)
    power_play_points = Column(Integer, nullable=False, default=0)
    power_play_time_on_ice = Column(Integer, nullable=False, default=0)  # seconds
    
    short_handed_goals = Column(Integer, nullable=False, default=0)
    short_handed_assists = Column(Integer, nullable=False, default=0)
    short_handed_points = Column(Integer, nullable=False, default=0)
    short_handed_time_on_ice = Column(Integer, nullable=False, default=0)  # seconds
    
    # Other Statistics
    game_winning_goals = Column(Integer, nullable=False, default=0)
    overtime_goals = Column(Integer, nullable=False, default=0)
    hits = Column(Integer, nullable=False, default=0)
    blocked_shots = Column(Integer, nullable=False, default=0)
    faceoff_wins = Column(Integer, nullable=False, default=0)
    faceoff_taken = Column(Integer, nullable=False, default=0)
    
    # Goalie-specific statistics (for goalies only)
    wins = Column(Integer, nullable=True)
    losses = Column(Integer, nullable=True)
    overtime_losses = Column(Integer, nullable=True)
    saves = Column(Integer, nullable=True)
    shots_against = Column(Integer, nullable=True)
    goals_against = Column(Integer, nullable=True)
    goals_against_average = Column(Float, nullable=True)
    save_percentage = Column(Float, nullable=True)
    shutouts = Column(Integer, nullable=True)
    
    # Advanced goalie statistics
    quality_starts = Column(Integer, nullable=True)
    really_bad_starts = Column(Integer, nullable=True)
    goals_saved_above_expected = Column(Float, nullable=True)
    
    # Salary Information (if available)
    salary = Column(Integer, nullable=True)  # USD
    cap_hit = Column(Integer, nullable=True)  # USD
    
    # Additional metadata
    rookie_season = Column(Boolean, nullable=False, default=False)
    
    def __repr__(self):
        return f"<PlayerSeason(player='{self.player.full_name}', season='{self.season}')>"
    
    @property
    def faceoff_percentage(self):
        """Calculate faceoff win percentage."""
        if self.faceoff_taken == 0:
            return 0.0
        return round((self.faceoff_wins / self.faceoff_taken) * 100, 1)
    
    @property
    def power_play_percentage(self):
        """Calculate power play goal percentage (goals per opportunity)."""
        # This would require power play opportunities data
        return None
    
    @property
    def points_per_game(self):
        """Calculate points per game."""
        if self.games_played == 0:
            return 0.0
        return round(self.points / self.games_played, 2)
    
    @property
    def goals_per_game(self):
        """Calculate goals per game."""
        if self.games_played == 0:
            return 0.0
        return round(self.goals / self.games_played, 2)
    
    @property
    def average_time_on_ice_seconds(self):
        """Calculate average time on ice per game in seconds."""
        if self.games_played == 0:
            return 0
        return self.time_on_ice_total_seconds // self.games_played