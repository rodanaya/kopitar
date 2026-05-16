"""
Fatigue Analysis Database Models

Models for tracking player fatigue metrics and travel data.
"""

from sqlalchemy import (
    Column, Integer, String, Boolean, Float, ForeignKey, DateTime, Text, Enum
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime, timedelta
import enum

from .base import BaseModel, AuditMixin


class TravelType(enum.Enum):
    """Travel type enumeration."""
    BUS = "bus"
    FLIGHT = "flight"
    CHARTER = "charter"
    COMMERCIAL = "commercial"


class PlayerFatigueMetrics(BaseModel, AuditMixin):
    """
    Comprehensive fatigue metrics for players.
    """
    
    __tablename__ = 'player_fatigue_metrics'
    
    # Relationships
    player_id = Column(Integer, ForeignKey('players.id'), nullable=False, index=True)
    player = relationship("Player", back_populates="fatigue_metrics")
    
    game_id = Column(Integer, ForeignKey('games.id'), nullable=False, index=True)
    game = relationship("Game")
    
    team_id = Column(Integer, ForeignKey('teams.id'), nullable=False, index=True)
    team = relationship("Team")
    
    # Date for which fatigue is calculated (game date)
    calculation_date = Column(DateTime, nullable=False, index=True)
    
    # Workload Factors (trailing windows)
    games_last_7_days = Column(Integer, nullable=False, default=0)
    games_last_14_days = Column(Integer, nullable=False, default=0)
    games_last_30_days = Column(Integer, nullable=False, default=0)
    
    # Time on Ice (seconds)
    toi_last_3_games = Column(Integer, nullable=False, default=0)
    toi_last_7_days = Column(Integer, nullable=False, default=0)
    toi_last_14_days = Column(Integer, nullable=False, default=0)
    
    # Rest and Recovery
    days_since_last_game = Column(Float, nullable=False, default=0.0)
    consecutive_games = Column(Integer, nullable=False, default=0)
    back_to_back_games = Column(Integer, nullable=False, default=0)  # Last 14 days
    
    # Travel Factors
    miles_traveled_last_7_days = Column(Float, nullable=False, default=0.0)
    miles_traveled_last_14_days = Column(Float, nullable=False, default=0.0)
    timezone_changes_last_7_days = Column(Integer, nullable=False, default=0)
    eastward_travel_hours = Column(Float, nullable=False, default=0.0)  # Last 7 days
    
    # Schedule Density
    three_in_four_nights = Column(Boolean, nullable=False, default=False)
    four_in_six_nights = Column(Boolean, nullable=False, default=False)
    games_in_last_10_days = Column(Integer, nullable=False, default=0)
    
    # Performance Context
    shots_faced_last_3_games = Column(Integer, nullable=True)  # Goalies only
    high_danger_shots_last_3_games = Column(Integer, nullable=True)  # Goalies only
    save_attempts_last_3_games = Column(Integer, nullable=True)  # Goalies only
    
    # Age and Experience Factors
    player_age_at_game = Column(Float, nullable=True)
    nhl_experience_years = Column(Float, nullable=True)
    
    # Injury and Health
    injury_report_status = Column(String(50), nullable=True)  # "healthy", "day-to-day", etc.
    missed_practice_last_week = Column(Boolean, nullable=False, default=False)
    
    # Calculated Fatigue Indices
    base_fatigue_index = Column(Float, nullable=False, default=0.0)  # 0-100 scale
    travel_fatigue_index = Column(Float, nullable=False, default=0.0)
    workload_fatigue_index = Column(Float, nullable=False, default=0.0)
    composite_fatigue_index = Column(Float, nullable=False, default=0.0)
    
    # Position-Specific Adjustments
    position_adjustment = Column(Float, nullable=False, default=1.0)
    goalie_workload_multiplier = Column(Float, nullable=True)  # Goalies only
    
    # Team Context
    team_back_to_back = Column(Boolean, nullable=False, default=False)
    home_stand_game_number = Column(Integer, nullable=True)  # Game # in current home stand
    road_trip_game_number = Column(Integer, nullable=True)  # Game # in current road trip
    
    # External Factors
    altitude_change = Column(Float, nullable=True)  # Feet above sea level change
    temperature_change = Column(Float, nullable=True)  # Temperature differential
    
    # Model Predictions (from fatigue index)
    predicted_performance_drop = Column(Float, nullable=True)  # % performance decrease
    confidence_interval_lower = Column(Float, nullable=True)
    confidence_interval_upper = Column(Float, nullable=True)
    
    def __repr__(self):
        return f"<PlayerFatigueMetrics(player_id={self.player_id}, date={self.calculation_date.date()})>"
    
    @property
    def fatigue_category(self):
        """Categorize fatigue level."""
        if self.composite_fatigue_index < 20:
            return "low"
        elif self.composite_fatigue_index < 40:
            return "moderate"
        elif self.composite_fatigue_index < 60:
            return "high"
        elif self.composite_fatigue_index < 80:
            return "very_high"
        else:
            return "extreme"
    
    @property
    def is_high_risk(self):
        """Check if player is at high risk for fatigue impact."""
        return self.composite_fatigue_index >= 60
    
    @property
    def rest_recommendation(self):
        """Get rest recommendation based on fatigue."""
        if self.composite_fatigue_index >= 80:
            return "mandatory_rest"
        elif self.composite_fatigue_index >= 60:
            return "strongly_recommended"
        elif self.composite_fatigue_index >= 40:
            return "consider_rest"
        else:
            return "no_action_needed"
    
    def calculate_recovery_time(self):
        """Estimate recovery time needed."""
        base_recovery = self.composite_fatigue_index * 0.1  # Hours
        
        # Age adjustment
        if self.player_age_at_game and self.player_age_at_game > 30:
            age_factor = 1 + ((self.player_age_at_game - 30) * 0.05)
            base_recovery *= age_factor
        
        # Travel adjustment
        if self.timezone_changes_last_7_days > 2:
            base_recovery *= 1.3
        
        return round(base_recovery, 1)


class TravelLog(BaseModel, AuditMixin):
    """
    Detailed travel tracking for teams and fatigue analysis.
    """
    
    __tablename__ = 'travel_logs'
    
    # Relationships
    team_id = Column(Integer, ForeignKey('teams.id'), nullable=False, index=True)
    team = relationship("Team", back_populates="travel_logs")
    
    game_id = Column(Integer, ForeignKey('games.id'), nullable=True, index=True)
    game = relationship("Game", back_populates="travel_logs")
    
    # Travel Details
    departure_city = Column(String(100), nullable=False)
    arrival_city = Column(String(100), nullable=False)
    departure_venue_id = Column(Integer, ForeignKey('venues.id'), nullable=True)
    arrival_venue_id = Column(Integer, ForeignKey('venues.id'), nullable=True)
    
    # Timing
    departure_date = Column(DateTime, nullable=False, index=True)
    departure_time = Column(DateTime, nullable=True)
    arrival_date = Column(DateTime, nullable=False)
    arrival_time = Column(DateTime, nullable=True)
    
    # Travel Specifics
    travel_type = Column(Enum(TravelType), nullable=False)
    distance_miles = Column(Float, nullable=False)
    flight_duration_minutes = Column(Integer, nullable=True)
    
    # Timezone Information
    departure_timezone = Column(String(50), nullable=False)
    arrival_timezone = Column(String(50), nullable=False)
    timezone_change_hours = Column(Float, nullable=False, default=0.0)
    eastward_travel = Column(Boolean, nullable=False, default=False)
    
    # Travel Quality Factors
    charter_flight = Column(Boolean, nullable=False, default=True)
    commercial_flight = Column(Boolean, nullable=False, default=False)
    delays_minutes = Column(Integer, nullable=False, default=0)
    layovers = Column(Integer, nullable=False, default=0)
    
    # Context
    back_to_back_travel = Column(Boolean, nullable=False, default=False)
    same_day_game = Column(Boolean, nullable=False, default=False)
    road_trip_game_number = Column(Integer, nullable=True)
    
    # Environmental Factors
    departure_altitude = Column(Float, nullable=True)  # Feet above sea level
    arrival_altitude = Column(Float, nullable=True)
    altitude_change = Column(Float, nullable=True)
    
    departure_temperature = Column(Float, nullable=True)  # Fahrenheit
    arrival_temperature = Column(Float, nullable=True)
    temperature_change = Column(Float, nullable=True)
    
    # Team Status
    players_traveling = Column(Integer, nullable=True)
    injured_players = Column(Integer, nullable=False, default=0)
    
    # Calculated Impact Scores
    travel_difficulty_score = Column(Float, nullable=False, default=0.0)  # 0-100
    fatigue_impact_score = Column(Float, nullable=False, default=0.0)
    
    # Additional Data
    notes = Column(Text, nullable=True)
    travel_details = Column(JSONB, nullable=True)  # Flexible additional data
    
    def __repr__(self):
        return f"<TravelLog(team_id={self.team_id}, {self.departure_city} → {self.arrival_city})>"
    
    @property
    def travel_duration_hours(self):
        """Calculate total travel duration in hours."""
        if not self.departure_time or not self.arrival_time:
            return None
        
        duration = self.arrival_time - self.departure_time
        return round(duration.total_seconds() / 3600, 1)
    
    @property
    def is_long_distance(self):
        """Check if this is a long-distance travel (>1000 miles)."""
        return self.distance_miles > 1000
    
    @property
    def is_cross_country(self):
        """Check if this is cross-country travel (>2000 miles)."""
        return self.distance_miles > 2000
    
    @property
    def jet_lag_risk(self):
        """Calculate jet lag risk category."""
        tz_change = abs(self.timezone_change_hours)
        
        if tz_change == 0:
            return "none"
        elif tz_change <= 1:
            return "minimal"
        elif tz_change <= 2:
            return "moderate"
        elif tz_change <= 3:
            return "significant"
        else:
            return "severe"
    
    def calculate_travel_score(self):
        """
        Calculate comprehensive travel difficulty score.
        
        Returns:
            float: Travel difficulty score (0-100)
        """
        score = 0.0
        
        # Distance component (0-30 points)
        distance_score = min(30, (self.distance_miles / 3000) * 30)
        score += distance_score
        
        # Timezone component (0-25 points)
        tz_score = abs(self.timezone_change_hours) * 5
        if self.eastward_travel:
            tz_score *= 1.5  # Eastward travel is harder
        score += min(25, tz_score)
        
        # Timing component (0-20 points)
        if self.same_day_game:
            score += 20
        elif self.back_to_back_travel:
            score += 15
        
        # Travel quality (0-15 points)
        if not self.charter_flight:
            score += 10
        if self.layovers > 0:
            score += 5
        if self.delays_minutes > 60:
            score += 5
        
        # Environmental factors (0-10 points)
        if self.altitude_change and abs(self.altitude_change) > 3000:
            score += 5
        if self.temperature_change and abs(self.temperature_change) > 30:
            score += 5
        
        return min(100, round(score, 1))