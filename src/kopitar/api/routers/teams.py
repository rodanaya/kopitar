"""
Teams API Router

Endpoints for team-related operations including statistics,
roster management, and schedule analysis.
"""

from typing import List, Optional, Dict, Any
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from fastapi.responses import JSONResponse

from ..schemas.teams import (
    TeamResponse, TeamStatsResponse, TeamScheduleResponse
)
from ..schemas.common import PaginationParams, SeasonParam
from ..dependencies import get_db_session, get_cache
from ..services.teams import TeamService
from ..services.schedule import ScheduleAnalysisService

router = APIRouter()


@router.get("/", response_model=List[TeamResponse])
async def get_teams(
    active_only: bool = Query(True, description="Only active teams"),
    conference: Optional[str] = Query(None, description="Filter by conference"),
    division: Optional[str] = Query(None, description="Filter by division"),
    pagination: PaginationParams = Depends(),
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """
    Get list of NHL teams with optional filtering.
    
    - **active_only**: Include only currently active teams
    - **conference**: Filter by conference (Eastern, Western)
    - **division**: Filter by division
    """
    team_service = TeamService(db_session, cache)
    
    teams = await team_service.get_teams(
        active_only=active_only,
        conference=conference,
        division=division,
        offset=pagination.offset,
        limit=pagination.limit
    )
    
    return teams


@router.get("/{team_id}", response_model=TeamResponse)
async def get_team(
    team_id: int = Path(..., description="NHL Team ID"),
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """
    Get detailed information for a specific team.
    """
    team_service = TeamService(db_session, cache)
    
    team = await team_service.get_team_by_id(team_id)
    
    if not team:
        raise HTTPException(
            status_code=404,
            detail=f"Team with ID {team_id} not found"
        )
    
    return team


@router.get("/{team_id}/stats", response_model=TeamStatsResponse)
async def get_team_stats(
    team_id: int = Path(..., description="NHL Team ID"),
    season: Optional[str] = SeasonParam,
    stat_type: str = Query("regular", description="Stats type (regular, playoff, advanced)"),
    include_fatigue: bool = Query(False, description="Include fatigue metrics"),
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """
    Get comprehensive statistics for a team.
    
    - **season**: Specific season (e.g., "20232024") or None for current season
    - **stat_type**: Type of statistics to retrieve
    - **include_fatigue**: Include team fatigue analysis
    """
    team_service = TeamService(db_session, cache)
    
    stats = await team_service.get_team_stats(
        team_id=team_id,
        season=season,
        stat_type=stat_type,
        include_fatigue=include_fatigue
    )
    
    if not stats:
        raise HTTPException(
            status_code=404,
            detail=f"Stats not found for team {team_id}"
        )
    
    return stats


@router.get("/{team_id}/roster", response_model=List[Dict[str, Any]])
async def get_team_roster(
    team_id: int = Path(..., description="NHL Team ID"),
    season: Optional[str] = SeasonParam,
    include_prospects: bool = Query(False, description="Include prospect players"),
    include_stats: bool = Query(True, description="Include player statistics"),
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """
    Get current roster for a team.
    
    Returns detailed roster information including player statistics.
    """
    team_service = TeamService(db_session, cache)
    
    roster = await team_service.get_roster(
        team_id=team_id,
        season=season,
        include_prospects=include_prospects,
        include_stats=include_stats
    )
    
    return roster


@router.get("/{team_id}/schedule", response_model=TeamScheduleResponse)
async def get_team_schedule(
    team_id: int = Path(..., description="NHL Team ID"),
    season: Optional[str] = SeasonParam,
    date_from: Optional[date] = Query(None, description="Start date"),
    date_to: Optional[date] = Query(None, description="End date"),
    include_analysis: bool = Query(True, description="Include schedule analysis"),
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """
    Get team schedule with fatigue and travel analysis.
    
    - **date_from**: Filter games from this date
    - **date_to**: Filter games to this date
    - **include_analysis**: Include schedule difficulty analysis
    """
    schedule_service = ScheduleAnalysisService(db_session, cache)
    
    schedule = await schedule_service.get_team_schedule(
        team_id=team_id,
        season=season,
        date_from=date_from,
        date_to=date_to,
        include_analysis=include_analysis
    )
    
    if not schedule:
        raise HTTPException(
            status_code=404,
            detail=f"Schedule not found for team {team_id}"
        )
    
    return schedule


@router.get("/{team_id}/fatigue-analysis", response_model=Dict[str, Any])
async def get_team_fatigue_analysis(
    team_id: int = Path(..., description="NHL Team ID"),
    analysis_date: Optional[date] = Query(None, description="Analysis date"),
    window_days: int = Query(14, ge=7, le=30, description="Analysis window in days"),
    include_predictions: bool = Query(False, description="Include fatigue predictions"),
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """
    Get comprehensive team fatigue analysis.
    
    Analyzes team-wide fatigue patterns and impacts on performance.
    """
    team_service = TeamService(db_session, cache)
    
    fatigue_analysis = await team_service.get_fatigue_analysis(
        team_id=team_id,
        analysis_date=analysis_date,
        window_days=window_days,
        include_predictions=include_predictions
    )
    
    return fatigue_analysis


@router.get("/{team_id}/travel-log", response_model=List[Dict[str, Any]])
async def get_team_travel_log(
    team_id: int = Path(..., description="NHL Team ID"),
    season: Optional[str] = SeasonParam,
    limit: int = Query(50, ge=1, le=200, description="Maximum entries to return"),
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """
    Get team travel log with distance and timezone analysis.
    """
    schedule_service = ScheduleAnalysisService(db_session, cache)
    
    travel_log = await schedule_service.get_travel_log(
        team_id=team_id,
        season=season,
        limit=limit
    )
    
    return travel_log


@router.get("/{team_id}/back-to-back-analysis", response_model=Dict[str, Any])
async def get_back_to_back_analysis(
    team_id: int = Path(..., description="NHL Team ID"),
    season: Optional[str] = SeasonParam,
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """
    Analyze team performance in back-to-back games.
    
    Provides detailed analysis of how the team performs in consecutive games.
    """
    team_service = TeamService(db_session, cache)
    
    b2b_analysis = await team_service.get_back_to_back_analysis(
        team_id=team_id,
        season=season
    )
    
    return b2b_analysis


@router.get("/{team_id}/standings", response_model=Dict[str, Any])
async def get_team_standings(
    team_id: int = Path(..., description="NHL Team ID"),
    season: Optional[str] = SeasonParam,
    include_projections: bool = Query(False, description="Include playoff projections"),
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """
    Get team standings information with context.
    
    Includes division, conference, and league standings with trends.
    """
    team_service = TeamService(db_session, cache)
    
    standings = await team_service.get_standings_info(
        team_id=team_id,
        season=season,
        include_projections=include_projections
    )
    
    return standings


@router.get("/{team_id}/performance-trends", response_model=Dict[str, Any])
async def get_performance_trends(
    team_id: int = Path(..., description="NHL Team ID"),
    season: Optional[str] = SeasonParam,
    window_size: int = Query(10, ge=5, le=25, description="Rolling window size"),
    metrics: List[str] = Query(
        ["goals_for", "goals_against", "shots_for", "save_percentage"],
        description="Metrics to analyze"
    ),
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """
    Analyze team performance trends over time.
    
    Provides rolling averages and trend analysis for key metrics.
    """
    team_service = TeamService(db_session, cache)
    
    trends = await team_service.get_performance_trends(
        team_id=team_id,
        season=season,
        window_size=window_size,
        metrics=metrics
    )
    
    return trends


@router.get("/{team_id}/line-combinations", response_model=Dict[str, Any])
async def get_line_combinations(
    team_id: int = Path(..., description="NHL Team ID"),
    season: Optional[str] = SeasonParam,
    include_performance: bool = Query(True, description="Include line performance stats"),
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """
    Get team line combinations and their performance.
    
    Analyzes forward lines, defensive pairings, and special teams units.
    """
    team_service = TeamService(db_session, cache)
    
    lines = await team_service.get_line_combinations(
        team_id=team_id,
        season=season,
        include_performance=include_performance
    )
    
    return lines


@router.post("/{team_id}/refresh-data")
async def refresh_team_data(
    team_id: int = Path(..., description="NHL Team ID"),
    force: bool = Query(False, description="Force refresh even if recently updated"),
    db_session = Depends(get_db_session)
):
    """
    Trigger refresh of team data from NHL API.
    
    Updates roster, schedule, and recent game statistics.
    """
    team_service = TeamService(db_session)
    
    # Trigger data refresh
    result = await team_service.refresh_team_data(
        team_id=team_id,
        force=force
    )
    
    return {
        "message": f"Data refresh initiated for team {team_id}",
        "status": "success",
        "updated_at": result.get("updated_at")
    }