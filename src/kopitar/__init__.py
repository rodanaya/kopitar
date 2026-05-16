"""
Kopitar NHL Analytics Platform

A comprehensive data science platform for analyzing NHL player performance,
fatigue patterns, and career trajectories across all positions.
"""

__version__ = "1.0.0"
__author__ = "Kopitar Team"
__email__ = "team@kopitar.dev"

try:
    from .api import NHLAPIClient
except Exception:  # pragma: no cover
    NHLAPIClient = None  # type: ignore[assignment,misc]

try:
    from .models import Player, Game, Team
except Exception:  # pragma: no cover
    Player = Game = Team = None  # type: ignore[assignment,misc]

try:
    from .analysis import FatigueAnalyzer, PerformanceAnalyzer
except Exception:  # pragma: no cover
    FatigueAnalyzer = PerformanceAnalyzer = None  # type: ignore[assignment,misc]

__all__ = [
    "NHLAPIClient",
    "Player",
    "Game",
    "Team",
    "FatigueAnalyzer",
    "PerformanceAnalyzer",
]