"""
Travel Calculator Engine

Calculates distances, timezone changes, and travel difficulty scores between
NHL arenas.  All logic is pure Python + stdlib only — haversine is implemented
inline without external libraries.
"""

from __future__ import annotations

import math
from datetime import date
from typing import Any


# ---------------------------------------------------------------------------
# Arena reference data (all 32 NHL teams)
# ---------------------------------------------------------------------------

ARENA_COORDS: dict[str, tuple[float, float]] = {
    "BOS": (42.3662, -71.0621),   # TD Garden
    "BUF": (42.8749, -78.8765),   # KeyBank Center
    "DET": (42.3410, -83.0551),   # Little Caesars Arena
    "FLA": (26.1584, -80.3258),   # Amerant Bank Arena
    "MTL": (45.4961, -73.5694),   # Bell Centre
    "OTT": (45.2965, -75.9270),   # Canadian Tire Centre
    "TBL": (27.9428, -82.4519),   # Amalie Arena
    "TOR": (43.6435, -79.3791),   # Scotiabank Arena
    "CAR": (35.8031, -78.7228),   # PNC Arena
    "CBJ": (39.9693, -83.0061),   # Nationwide Arena
    "NJD": (40.7335, -74.1712),   # Prudential Center
    "NYI": (40.7228, -73.5903),   # UBS Arena
    "NYR": (40.7505, -73.9934),   # Madison Square Garden
    "PHI": (39.9012, -75.1720),   # Wells Fargo Center
    "PIT": (40.4396, -79.9892),   # PPG Paints Arena
    "WSH": (38.8981, -77.0209),   # Capital One Arena
    "CHI": (41.8807, -87.6742),   # United Center
    "COL": (39.7486, -105.0078),  # Ball Arena
    "DAL": (32.7905, -96.8100),   # American Airlines Center
    "MIN": (44.9449, -93.1010),   # Xcel Energy Center
    "NSH": (36.1591, -86.7785),   # Bridgestone Arena
    "STL": (38.6267, -90.2028),   # Enterprise Center
    "WPG": (49.8928, -97.1439),   # Canada Life Centre
    "ANA": (33.8078, -117.8763),  # Honda Center
    "UTA": (40.7683, -111.9011),  # Delta Center, Salt Lake City
    "CGY": (51.0375, -114.0514),  # Scotiabank Saddledome
    "EDM": (53.5461, -113.4938),  # Rogers Place
    "LAK": (34.0430, -118.2673),  # Crypto.com Arena
    "SJS": (37.3329, -121.9010),  # SAP Center
    "SEA": (47.6216, -122.3544),  # Climate Pledge Arena
    "VGK": (36.1028, -115.1784),  # T-Mobile Arena
    "VAN": (49.2778, -123.1088),  # Rogers Arena
}

ARENA_TIMEZONES: dict[str, str] = {
    "BOS": "America/New_York",
    "BUF": "America/New_York",
    "DET": "America/Detroit",
    "FLA": "America/New_York",
    "MTL": "America/Toronto",
    "OTT": "America/Toronto",
    "TBL": "America/New_York",
    "TOR": "America/Toronto",
    "CAR": "America/New_York",
    "CBJ": "America/New_York",
    "NJD": "America/New_York",
    "NYI": "America/New_York",
    "NYR": "America/New_York",
    "PHI": "America/New_York",
    "PIT": "America/New_York",
    "WSH": "America/New_York",
    "CHI": "America/Chicago",
    "COL": "America/Denver",
    "DAL": "America/Chicago",
    "MIN": "America/Chicago",
    "NSH": "America/Chicago",
    "STL": "America/Chicago",
    "WPG": "America/Winnipeg",
    "ANA": "America/Los_Angeles",
    "UTA": "America/Denver",
    "CGY": "America/Edmonton",
    "EDM": "America/Edmonton",
    "LAK": "America/Los_Angeles",
    "SJS": "America/Los_Angeles",
    "SEA": "America/Los_Angeles",
    "VGK": "America/Los_Angeles",
    "VAN": "America/Vancouver",
}

# Static UTC offsets (hours) for each timezone during standard time.
# Phoenix (ARI) does not observe DST, so it is always UTC-7.
# During DST seasons most North American arenas shift by +1 hour, but since
# we only care about the *relative* difference between arenas in the same
# country/continent the error introduced is small and symmetric.  We use
# standard-time offsets because the NHL regular season straddles both
# periods and a fixed offset is more predictable for fatigue modelling.
_TZ_UTC_OFFSET: dict[str, float] = {
    "America/New_York":    -5.0,
    "America/Detroit":     -5.0,
    "America/Toronto":     -5.0,
    "America/Chicago":     -6.0,
    "America/Winnipeg":    -6.0,
    "America/Denver":      -7.0,
    "America/Phoenix":     -7.0,
    "America/Los_Angeles": -8.0,
    "America/Vancouver":   -8.0,
    "America/Edmonton":    -7.0,
    "America/Montreal":    -5.0,
}

# Earth radius in miles (mean radius)
_EARTH_RADIUS_MILES: float = 3_958.8


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------

class TravelCalculator:
    """
    Calculates travel distances and fatigue impact between NHL arenas.

    All distance calculations use the haversine great-circle formula
    implemented inline (no external libraries required).
    """

    # ------------------------------------------------------------------
    # Core distance & direction methods
    # ------------------------------------------------------------------

    def calculate_distance(self, from_abbrev: str, to_abbrev: str) -> float:
        """
        Calculate the great-circle distance in miles between two NHL arenas.

        Parameters
        ----------
        from_abbrev:
            Three-letter NHL team abbreviation of the origin arena.
        to_abbrev:
            Three-letter NHL team abbreviation of the destination arena.

        Returns
        -------
        float
            Distance in miles.  Returns 0.0 if either abbreviation is unknown.
        """
        from_coords = ARENA_COORDS.get(from_abbrev.upper())
        to_coords = ARENA_COORDS.get(to_abbrev.upper())

        if from_coords is None or to_coords is None:
            return 0.0

        return _haversine_miles(from_coords, to_coords)

    def calculate_timezone_change(
        self, from_abbrev: str, to_abbrev: str
    ) -> float:
        """
        Calculate the timezone offset difference between two arenas in hours.

        A positive result means the destination is *east* of the origin (later
        clock time); a negative result means the destination is *west*.

        Parameters
        ----------
        from_abbrev:
            Three-letter NHL team abbreviation of the origin arena.
        to_abbrev:
            Three-letter NHL team abbreviation of the destination arena.

        Returns
        -------
        float
            Timezone difference in hours (destination offset − origin offset).
            Returns 0.0 if either abbreviation is unknown.
        """
        from_tz = ARENA_TIMEZONES.get(from_abbrev.upper())
        to_tz = ARENA_TIMEZONES.get(to_abbrev.upper())

        if from_tz is None or to_tz is None:
            return 0.0

        from_offset = _TZ_UTC_OFFSET.get(from_tz, 0.0)
        to_offset = _TZ_UTC_OFFSET.get(to_tz, 0.0)

        # Positive = moved east (later local time at destination)
        return to_offset - from_offset

    def is_eastward(self, from_abbrev: str, to_abbrev: str) -> bool:
        """
        Return True if travelling from *from_abbrev* to *to_abbrev* is eastward.

        Eastward is defined as the destination having a *greater* (less negative)
        longitude than the origin, i.e. moving toward the right on a standard
        map of North America.

        Parameters
        ----------
        from_abbrev:
            Three-letter NHL team abbreviation of the origin arena.
        to_abbrev:
            Three-letter NHL team abbreviation of the destination arena.

        Returns
        -------
        bool
            True if the trip is eastward, False otherwise (including unknown).
        """
        from_coords = ARENA_COORDS.get(from_abbrev.upper())
        to_coords = ARENA_COORDS.get(to_abbrev.upper())

        if from_coords is None or to_coords is None:
            return False

        from_lon = from_coords[1]
        to_lon = to_coords[1]

        # Handle antimeridian wrap-around
        diff = to_lon - from_lon
        if diff > 180:
            diff -= 360
        elif diff < -180:
            diff += 360

        # In North America all longitudes are negative; moving east means
        # longitude becomes *less negative* (increases).
        return diff > 0

    # ------------------------------------------------------------------
    # Trip difficulty scoring
    # ------------------------------------------------------------------

    def calculate_trip_difficulty(
        self,
        legs: list[tuple[str, str]],
        game_date: date,
    ) -> float:
        """
        Calculate a 0-100 travel difficulty score for a multi-leg trip.

        Formula per leg::

            difficulty = distance/3000*30
                       + abs(tz_change)*5*(1.5 if eastward else 1.0)
                       + same_day_game*20

        "Same-day game" is True when the trip date equals *game_date*.
        The total difficulty across all legs is clamped to [0, 100].

        Parameters
        ----------
        legs:
            List of ``(from_abbrev, to_abbrev)`` tuples describing each
            travel segment.
        game_date:
            The date on which the game is played; used to apply the
            same-day travel penalty on the final leg.

        Returns
        -------
        float
            Total trip difficulty score in [0, 100].
        """
        total = 0.0
        n_legs = len(legs)

        for i, (frm, to) in enumerate(legs):
            distance = self.calculate_distance(frm, to)
            tz_change = self.calculate_timezone_change(frm, to)
            eastward = self.is_eastward(frm, to)

            # Same-day game penalty applies only on the final leg
            same_day = (i == n_legs - 1)

            distance_component = (distance / 3000.0) * 30.0
            tz_component = abs(tz_change) * 5.0 * (1.5 if eastward else 1.0)
            timing_component = 20.0 if same_day else 0.0

            total += distance_component + tz_component + timing_component

        return min(100.0, round(total, 2))

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    def get_arena_coords(self, abbrev: str) -> tuple[float, float] | None:
        """Return ``(lat, lon)`` for *abbrev*, or None if unknown."""
        return ARENA_COORDS.get(abbrev.upper())

    def get_arena_timezone(self, abbrev: str) -> str | None:
        """Return the IANA timezone string for *abbrev*, or None if unknown."""
        return ARENA_TIMEZONES.get(abbrev.upper())

    def estimate_flight_hours(self, from_abbrev: str, to_abbrev: str) -> float:
        """
        Estimate total travel time in hours (flight + ground logistics).

        Formula: distance / 500 mph + 2 hr buffer.

        Returns 0.0 if distance is 0 (same city or unknown arenas).
        """
        distance = self.calculate_distance(from_abbrev, to_abbrev)
        if distance <= 0:
            return 0.0
        return round(distance / 500.0 + 2.0, 2)

    def all_team_abbreviations(self) -> list[str]:
        """Return a sorted list of all known team abbreviations."""
        return sorted(ARENA_COORDS.keys())


# ---------------------------------------------------------------------------
# Pure-Python haversine implementation
# ---------------------------------------------------------------------------

def _haversine_miles(
    point1: tuple[float, float],
    point2: tuple[float, float],
) -> float:
    """
    Calculate great-circle distance in miles between two (lat, lon) points.

    Uses the haversine formula.  Inputs in decimal degrees.
    """
    lat1, lon1 = math.radians(point1[0]), math.radians(point1[1])
    lat2, lon2 = math.radians(point2[0]), math.radians(point2[1])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))

    return _EARTH_RADIUS_MILES * c
