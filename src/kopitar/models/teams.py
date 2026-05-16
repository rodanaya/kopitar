"""
Team-related Database Models

Models for NHL teams, venues, divisions, and conferences.
"""

from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey, Text, Date
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from .base import BaseModel, AuditMixin


class Conference(BaseModel, AuditMixin):
    """
    NHL Conference model (Eastern, Western).
    """
    
    __tablename__ = 'conferences'
    
    # NHL Conference ID
    nhl_id = Column(Integer, unique=True, nullable=False, index=True)
    
    # Conference details
    name = Column(String(100), nullable=False)  # "Eastern Conference"
    abbreviation = Column(String(10), nullable=False)  # "E"
    short_name = Column(String(50), nullable=False)  # "Eastern"
    
    # Status
    active = Column(Boolean, nullable=False, default=True)
    
    # Relationships
    divisions = relationship("Division", back_populates="conference")
    teams = relationship("Team", back_populates="conference")
    
    def __repr__(self):
        return f"<Conference(name='{self.name}')>"


class Division(BaseModel, AuditMixin):
    """
    NHL Division model.
    """
    
    __tablename__ = 'divisions'
    
    # NHL Division ID
    nhl_id = Column(Integer, unique=True, nullable=False, index=True)
    
    # Division details
    name = Column(String(100), nullable=False)  # "Atlantic Division"
    name_short = Column(String(50), nullable=False)  # "Atlantic"
    abbreviation = Column(String(10), nullable=False)  # "ATL"
    
    # Conference relationship
    conference_id = Column(Integer, ForeignKey('conferences.id'), nullable=False)
    conference = relationship("Conference", back_populates="divisions")
    
    # Status
    active = Column(Boolean, nullable=False, default=True)
    
    # Relationships
    teams = relationship("Team", back_populates="division")
    
    def __repr__(self):
        return f"<Division(name='{self.name}')>"


class Venue(BaseModel, AuditMixin):
    """
    NHL Venue/Arena model with location data for travel calculations.
    """
    
    __tablename__ = 'venues'
    
    # NHL Venue ID
    nhl_id = Column(Integer, unique=True, nullable=True, index=True)
    
    # Venue details
    name = Column(String(200), nullable=False)  # "Bell Centre"
    city = Column(String(100), nullable=False)  # "Montreal"
    state_province = Column(String(50), nullable=True)  # "QC" or "Quebec"
    country = Column(String(50), nullable=False, default="Canada")
    
    # Geographic coordinates for travel calculations
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    
    # Timezone information
    timezone_id = Column(String(50), nullable=False)  # "America/Montreal"
    timezone_offset = Column(Integer, nullable=False)  # UTC offset in hours
    
    # Arena details
    capacity = Column(Integer, nullable=True)
    opened = Column(Integer, nullable=True)  # Year opened
    surface = Column(String(50), nullable=True, default="Ice")
    
    # Address and contact
    address = Column(Text, nullable=True)
    
    # Relationships
    teams = relationship("Team", back_populates="venue")
    home_games = relationship("Game", foreign_keys="Game.venue_id", back_populates="venue")
    
    def __repr__(self):
        return f"<Venue(name='{self.name}', city='{self.city}')>"
    
    def distance_to(self, other_venue):
        """
        Calculate great circle distance to another venue.
        
        Args:
            other_venue: Another Venue instance
            
        Returns:
            float: Distance in miles
        """
        from math import radians, sin, cos, sqrt, atan2
        
        # Earth's radius in miles
        R = 3959
        
        # Convert coordinates to radians
        lat1, lon1 = radians(self.latitude), radians(self.longitude)
        lat2, lon2 = radians(other_venue.latitude), radians(other_venue.longitude)
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        distance = R * c
        return round(distance, 2)


class Team(BaseModel, AuditMixin):
    """
    NHL Team model with franchise information.
    """
    
    __tablename__ = 'teams'
    
    # NHL Team ID
    nhl_id = Column(Integer, unique=True, nullable=False, index=True)
    
    # Team identification
    name = Column(String(200), nullable=False)  # "Montreal Canadiens"
    location_name = Column(String(100), nullable=False)  # "Montreal"
    team_name = Column(String(100), nullable=False)  # "Canadiens"
    abbreviation = Column(String(10), nullable=False)  # "MTL"
    tricode = Column(String(3), nullable=False, index=True)  # "MTL"
    
    # Organizational structure
    division_id = Column(Integer, ForeignKey('divisions.id'), nullable=False)
    division = relationship("Division", back_populates="teams")
    
    conference_id = Column(Integer, ForeignKey('conferences.id'), nullable=False)
    conference = relationship("Conference", back_populates="teams")
    
    # Venue
    venue_id = Column(Integer, ForeignKey('venues.id'), nullable=False)
    venue = relationship("Venue", back_populates="teams")
    
    # Franchise information
    franchise_id = Column(Integer, nullable=True)
    first_year_of_play = Column(String(8), nullable=True)  # "19091910"
    
    # Team branding
    primary_color = Column(String(7), nullable=True)  # Hex color "#FF0000"
    secondary_color = Column(String(7), nullable=True)
    logo_url = Column(String(500), nullable=True)
    
    # External links
    official_site_url = Column(String(500), nullable=True)
    twitter_hashtag = Column(String(50), nullable=True)
    
    # Status
    active = Column(Boolean, nullable=False, default=True)
    
    # Relationships
    players = relationship("Player", back_populates="current_team")
    player_seasons = relationship("PlayerSeason", back_populates="team")
    home_games = relationship("Game", foreign_keys="Game.home_team_id", back_populates="home_team")
    away_games = relationship("Game", foreign_keys="Game.away_team_id", back_populates="away_team")
    game_team_stats = relationship("GameTeamStats", back_populates="team")
    travel_logs = relationship("TravelLog", back_populates="team")
    
    def __repr__(self):
        return f"<Team(name='{self.name}', tricode='{self.tricode}')>"
    
    @property
    def full_name(self):
        """Get full team name."""
        return f"{self.location_name} {self.team_name}"
    
    def games_in_season(self, season):
        """
        Get all games for this team in a specific season.
        
        Args:
            season: Season string (e.g., "20232024")
            
        Returns:
            Query: Games for this team in the season
        """
        from .games import Game
        return Game.query.filter(
            Game.season == season,
            (Game.home_team_id == self.id) | (Game.away_team_id == self.id)
        )
    
    def current_roster(self, season=None):
        """
        Get current roster for the team.
        
        Args:
            season: Optional season filter
            
        Returns:
            Query: Current players on the team
        """
        from .players import PlayerSeason
        query = PlayerSeason.query.filter(PlayerSeason.team_id == self.id)
        
        if season:
            query = query.filter(PlayerSeason.season == season)
        
        return query