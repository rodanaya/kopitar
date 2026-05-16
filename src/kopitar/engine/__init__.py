"""
kopitar.engine
==============

Core fatigue calculation engine for the Kopitar NHL goaltender analysis
system.

Exports
-------
FatigueCalculator
    Calculates composite fatigue indices from player workload and travel
    history.  Entry point: :meth:`FatigueCalculator.calculate`.

TravelCalculator
    Calculates travel distances and difficulty scores between NHL arenas.
    Includes a full hardcoded database of all 32 arena coordinates and
    timezone offsets.

ScheduleAnalyzer
    Detects fatigue-relevant schedule patterns (back-to-back, three-in-four,
    four-in-six) and computes schedule density metrics.
"""

from .fatigue_calculator import FatigueCalculator, FatigueResult
from .travel_calculator import TravelCalculator, ARENA_COORDS, ARENA_TIMEZONES
from .schedule_analyzer import ScheduleAnalyzer

__all__ = [
    "FatigueCalculator",
    "FatigueResult",
    "TravelCalculator",
    "ARENA_COORDS",
    "ARENA_TIMEZONES",
    "ScheduleAnalyzer",
]
