"""
Common API Schemas

Shared Pydantic models used across multiple endpoints.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field, validator
from fastapi import Query


class PaginationParams(BaseModel):
    """Standard pagination parameters."""
    
    offset: int = Field(0, ge=0, description="Number of records to skip")
    limit: int = Field(50, ge=1, le=1000, description="Maximum records to return")
    
    @property
    def page_number(self) -> int:
        """Calculate page number from offset and limit."""
        return (self.offset // self.limit) + 1


class SortParams(BaseModel):
    """Standard sorting parameters."""
    
    sort_by: str = Field("id", description="Field to sort by")
    sort_order: str = Field("asc", pattern="^(asc|desc)$", description="Sort order")


class DateRangeParams(BaseModel):
    """Date range filtering parameters."""
    
    start_date: Optional[datetime] = Field(None, description="Start date")
    end_date: Optional[datetime] = Field(None, description="End date")
    
    @validator("end_date")
    def end_date_after_start(cls, v, values):
        """Ensure end date is after start date."""
        if v and "start_date" in values and values["start_date"]:
            if v < values["start_date"]:
                raise ValueError("End date must be after start date")
        return v


class ErrorResponse(BaseModel):
    """Standard error response format."""
    
    error: Dict[str, Any] = Field(
        ...,
        description="Error details",
        example={
            "type": "validation_error",
            "message": "Invalid input provided",
            "status_code": 400,
            "path": "/api/v1/players",
            "timestamp": 1640995200.0
        }
    )


class SuccessResponse(BaseModel):
    """Standard success response format."""
    
    success: bool = Field(True, description="Operation success flag")
    message: str = Field(..., description="Success message")
    data: Optional[Dict[str, Any]] = Field(None, description="Optional response data")
    timestamp: float = Field(..., description="Response timestamp")


class MetricsFilter(BaseModel):
    """Filter for selecting specific metrics."""
    
    include_basic: bool = Field(True, description="Include basic statistics")
    include_advanced: bool = Field(False, description="Include advanced metrics")
    include_fatigue: bool = Field(False, description="Include fatigue metrics")
    custom_metrics: Optional[List[str]] = Field(
        None, 
        description="Specific metrics to include"
    )


class PositionFilter(BaseModel):
    """Player position filtering."""
    
    positions: List[str] = Field(
        ["G", "D", "F"],
        description="Positions to include (G=Goalie, D=Defense, F=Forward)"
    )
    
    @validator("positions")
    def validate_positions(cls, v):
        """Ensure valid position codes."""
        valid_positions = {"G", "D", "F"}
        for position in v:
            if position not in valid_positions:
                raise ValueError(f"Invalid position: {position}")
        return v


class SeasonFilter(BaseModel):
    """Season filtering parameters."""
    
    seasons: List[str] = Field(
        [],
        description="Specific seasons to include (e.g., ['20232024', '20222023'])"
    )
    season_type: str = Field(
        "regular",
        pattern="^(regular|playoff|preseason|all)$",
        description="Type of season data"
    )
    
    @validator("seasons")
    def validate_season_format(cls, v):
        """Ensure proper season format."""
        for season in v:
            if len(season) != 8 or not season.isdigit():
                raise ValueError(f"Invalid season format: {season}")
            
            start_year = int(season[:4])
            end_year = int(season[4:])
            
            if end_year != start_year + 1:
                raise ValueError(f"Invalid season: {season}")
                
        return v


class CacheControl(BaseModel):
    """Cache control parameters."""
    
    use_cache: bool = Field(True, description="Whether to use cached data")
    cache_ttl: Optional[int] = Field(
        None, 
        ge=0, 
        description="Custom cache TTL in seconds"
    )
    force_refresh: bool = Field(
        False, 
        description="Force refresh from source"
    )


class AnalyticsParams(BaseModel):
    """Analytics and aggregation parameters."""
    
    aggregation_level: str = Field(
        "game",
        pattern="^(game|week|month|season|career)$",
        description="Level of data aggregation"
    )
    include_trends: bool = Field(
        False,
        description="Include trend analysis"
    )
    include_comparisons: bool = Field(
        False,
        description="Include peer comparisons"
    )
    min_games_threshold: int = Field(
        1,
        ge=1,
        description="Minimum games for inclusion in analysis"
    )


# Common query parameters for dependency injection
SeasonParam = Query(
    None, 
    pattern=r"^\d{8}$", 
    description="Season in YYYYYYYY format (e.g., 20232024)"
)

PositionParam = Query(
    None,
    pattern="^[GDF]$",
    description="Player position (G=Goalie, D=Defense, F=Forward)"
)

TeamParam = Query(
    None,
    ge=1,
    le=50,
    description="NHL Team ID"
)
