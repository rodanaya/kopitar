"""
Kopitar Data Models

SQLAlchemy models for the NHL analytics platform.
Designed to support 40+ years of data and advanced fatigue analysis.
"""

from .base import Base, BaseModel, AuditMixin
from .teams import Team, Venue, Division, Conference
from .players import Player, PlayerSeason
from .games import Game, GameTeamStats, Period
from .player_stats import PlayerGameStats, GoalieGameStats, PlayerAdvancedStats
from .fatigue import PlayerFatigueMetrics, TravelLog
from .predictions import Prediction, ModelPerformance
from .users import User, UserSession

__all__ = [
    # Base
    'Base',
    'BaseModel',
    'AuditMixin',
    
    # Teams and Organization
    'Team',
    'Venue', 
    'Division',
    'Conference',
    
    # Players
    'Player',
    'PlayerSeason',
    
    # Games
    'Game',
    'GameTeamStats',
    'Period',
    
    # Player Statistics
    'PlayerGameStats',
    'GoalieGameStats', 
    'PlayerAdvancedStats',
    
    # Fatigue Analysis
    'PlayerFatigueMetrics',
    'TravelLog',
    
    # Predictions and ML
    'Prediction',
    'ModelPerformance',
    
    # Users and Auth
    'User',
    'UserSession'
]