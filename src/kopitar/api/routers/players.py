"""
Players API Router

Endpoints for player-related operations including statistics,
fatigue analysis, and career information.
"""

from typing import List, Optional, Dict, Any
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, Path, BackgroundTasks
from fastapi.responses import JSONResponse

from ..schemas.players import (
    PlayerResponse, PlayerStatsResponse, PlayerFatigueResponse,
    PlayerSearchRequest, PlayerComparisonResponse
)
from ..schemas.common import PaginationParams, SeasonParam
from ..dependencies import get_current_user, get_db_session, get_cache
from ..services.players import PlayerService
from ..services.fatigue import FatigueAnalysisService
from ...models.players import Player

router = APIRouter()


@router.get("/", response_model=List[PlayerResponse])
async def get_players(
    position: Optional[str] = Query(None, description="Filter by position (G, D, F)"),
    team_id: Optional[int] = Query(None, description="Filter by team ID"),
    active_only: bool = Query(True, description="Only active players"),
    pagination: PaginationParams = Depends(),
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """
    Get list of NHL players with optional filtering.
    
    - **position**: Filter by position (G=Goalie, D=Defense, F=Forward)
    - **team_id**: Filter by specific team
    - **active_only**: Include only currently active players
    """
    player_service = PlayerService(db_session, cache)
    
    players = await player_service.get_players(
        position=position,
        team_id=team_id,
        active_only=active_only,
        offset=pagination.offset,
        limit=pagination.limit
    )
    
    return players


@router.get("/search", response_model=List[PlayerResponse])
async def search_players(
    query: str = Query(..., description="Search query (name, team, etc.)"),
    position: Optional[str] = Query(None, description="Filter by position"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """
    Search for players by name, team, or other criteria.
    """
    player_service = PlayerService(db_session, cache)
    
    results = await player_service.search_players(
        query=query,
        position=position,
        limit=limit
    )
    
    return results


@router.get("/{player_id}", response_model=PlayerResponse)
async def get_player(
    player_id: int = Path(..., description="NHL Player ID"),
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """
    Get detailed information for a specific player.
    """
    player_service = PlayerService(db_session, cache)
    
    player = await player_service.get_player_by_id(player_id)
    
    if not player:
        raise HTTPException(
            status_code=404,
            detail=f"Player with ID {player_id} not found"
        )
    
    return player


@router.get("/{player_id}/stats", response_model=PlayerStatsResponse)
async def get_player_stats(
    player_id: int = Path(..., description="NHL Player ID"),
    season: Optional[str] = SeasonParam,
    stat_type: str = Query("regular", description="Stats type (regular, playoff, advanced)"),
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """
    Get comprehensive statistics for a player.
    
    - **season**: Specific season (e.g., "20232024") or None for career stats
    - **stat_type**: Type of statistics to retrieve
    """
    player_service = PlayerService(db_session, cache)
    
    stats = await player_service.get_player_stats(
        player_id=player_id,
        season=season,
        stat_type=stat_type
    )
    
    if not stats:
        raise HTTPException(
            status_code=404,
            detail=f"Stats not found for player {player_id}"
        )
    
    return stats


@router.get("/{player_id}/fatigue", response_model=PlayerFatigueResponse)
async def get_player_fatigue(
    player_id: int = Path(..., description="NHL Player ID"),
    date: Optional[date] = Query(None, description="Specific date for fatigue analysis"),
    window_days: int = Query(10, ge=3, le=30, description="Analysis window in days"),
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """
    Get fatigue analysis for a player.
    
    - **date**: Specific date to analyze (defaults to latest available)
    - **window_days**: Number of days to include in analysis window
    """
    fatigue_service = FatigueAnalysisService(db_session, cache)
    
    fatigue_data = await fatigue_service.analyze_player_fatigue(
        player_id=player_id,
        target_date=date,
        window_days=window_days
    )
    
    if not fatigue_data:
        raise HTTPException(
            status_code=404,
            detail=f"Fatigue data not available for player {player_id}"
        )
    
    return fatigue_data


@router.get("/{player_id}/career", response_model=Dict[str, Any])
async def get_player_career(
    player_id: int = Path(..., description="NHL Player ID"),
    include_projections: bool = Query(False, description="Include career projections"),
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """
    Get comprehensive career analysis for a player.
    
    Includes career trajectory, peak performance periods, and optional projections.
    """
    player_service = PlayerService(db_session, cache)
    
    career_data = await player_service.get_career_analysis(
        player_id=player_id,
        include_projections=include_projections
    )
    
    if not career_data:
        raise HTTPException(
            status_code=404,
            detail=f"Career data not available for player {player_id}"
        )
    
    return career_data


@router.get("/{player_id}/game-log", response_model=List[Dict[str, Any]])
async def get_player_game_log(
    player_id: int = Path(..., description="NHL Player ID"),
    season: Optional[str] = SeasonParam,
    limit: int = Query(50, ge=1, le=200, description="Maximum games to return"),
    include_advanced: bool = Query(False, description="Include advanced statistics"),
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """
    Get game-by-game log for a player.
    
    Returns detailed game statistics with optional advanced metrics.
    """
    player_service = PlayerService(db_session, cache)
    
    game_log = await player_service.get_game_log(
        player_id=player_id,
        season=season,
        limit=limit,
        include_advanced=include_advanced
    )
    
    return game_log


@router.post("/compare", response_model=PlayerComparisonResponse)
async def compare_players(
    player_ids: List[int] = Query(..., description="List of player IDs to compare"),
    season: Optional[str] = SeasonParam,
    metrics: List[str] = Query(
        ["goals", "assists", "points"], 
        description="Metrics to compare"
    ),
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """
    Compare multiple players across specified metrics.
    
    - **player_ids**: List of 2-6 player IDs to compare
    - **season**: Season to compare (defaults to current)
    - **metrics**: Statistics to include in comparison
    """
    if len(player_ids) < 2 or len(player_ids) > 6:
        raise HTTPException(
            status_code=400,
            detail="Must compare between 2 and 6 players"
        )
    
    player_service = PlayerService(db_session, cache)
    
    comparison = await player_service.compare_players(
        player_ids=player_ids,
        season=season,
        metrics=metrics
    )
    
    return comparison


@router.get("/{player_id}/similar", response_model=List[PlayerResponse])
async def get_similar_players(
    player_id: int = Path(..., description="NHL Player ID"),
    limit: int = Query(10, ge=3, le=20, description="Number of similar players"),
    criteria: str = Query(
        "performance", 
        description="Similarity criteria (performance, style, career)"
    ),
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """
    Find players similar to the specified player.
    
    Uses machine learning to identify players with similar:
    - Performance patterns
    - Playing style
    - Career trajectories
    """
    player_service = PlayerService(db_session, cache)
    
    similar_players = await player_service.find_similar_players(
        player_id=player_id,
        limit=limit,
        criteria=criteria
    )
    
    return similar_players


@router.post("/{player_id}/refresh-data")
async def refresh_player_data(
    background_tasks: BackgroundTasks,
    player_id: int = Path(..., description="NHL Player ID"),
    force: bool = Query(False, description="Force refresh even if recently updated"),
    current_user = Depends(get_current_user),
    db_session = Depends(get_db_session)
):
    """
    Trigger refresh of player data from NHL API.
    
    Requires authentication and runs asynchronously.
    """
    player_service = PlayerService(db_session)
    
    # Add background task to refresh data
    background_tasks.add_task(
        player_service.refresh_player_data,
        player_id=player_id,
        force=force
    )
    
    return {
        "message": f"Data refresh initiated for player {player_id}",
        "status": "queued"
    }


@router.get("/{player_id}/predictions", response_model=Dict[str, Any])
async def get_player_predictions(
    player_id: int = Path(..., description="NHL Player ID"),
    prediction_type: str = Query(
        "performance", 
        description="Type of prediction (performance, fatigue, injury)"
    ),
    horizon_days: int = Query(7, ge=1, le=30, description="Prediction horizon"),
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """
    Get performance predictions for a player.
    
    Uses machine learning models to predict future performance.
    """
    player_service = PlayerService(db_session, cache)
    
    predictions = await player_service.get_predictions(
        player_id=player_id,
        prediction_type=prediction_type,
        horizon_days=horizon_days
    )
    
    if not predictions:
        raise HTTPException(
            status_code=404,
            detail=f"Predictions not available for player {player_id}"
        )
    
    return predictions
