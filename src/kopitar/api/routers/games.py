"""
Games API Router

Endpoints for game-related operations including live scores,
statistics, analysis, and event tracking.
"""

from typing import List, Optional, Dict, Any
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from fastapi.responses import JSONResponse

from ..schemas.games import (
    GameResponse, GameStatsResponse, GameSearchRequest, 
    GamePrediction, GameAnalysis
)
from ..schemas.common import PaginationParams, SeasonParam
from ..dependencies import get_db_session, get_cache
from ..services.games import GameService
from ..services.predictions import GamePredictionService

router = APIRouter()


@router.get("/", response_model=List[GameResponse])
async def get_games(
    date_from: Optional[date] = Query(None, description="Start date filter"),
    date_to: Optional[date] = Query(None, description="End date filter"),
    team_id: Optional[int] = Query(None, description="Filter by team"),
    season: Optional[str] = SeasonParam,
    game_type: Optional[str] = Query(None, description="Game type (R, P, PR, A)"),
    game_state: Optional[str] = Query(None, description="Game state filter"),
    pagination: PaginationParams = Depends(),
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """
    Get list of NHL games with filtering options.
    
    - **date_from**: Start date for game search
    - **date_to**: End date for game search  
    - **team_id**: Filter games involving specific team
    - **season**: Season filter (YYYYYYYY format)
    - **game_type**: R=Regular, P=Playoff, PR=Preseason, A=All-Star
    - **game_state**: scheduled, live, final, etc.
    """
    game_service = GameService(db_session, cache)
    
    games = await game_service.get_games(
        date_from=date_from,
        date_to=date_to,
        team_id=team_id,
        season=season,
        game_type=game_type,
        game_state=game_state,
        offset=pagination.offset,
        limit=pagination.limit
    )
    
    return games


@router.get("/today", response_model=List[GameResponse])
async def get_todays_games(
    include_live_data: bool = Query(True, description="Include live game data"),
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """
    Get today's NHL games with live updates.
    """
    game_service = GameService(db_session, cache)
    
    games = await game_service.get_todays_games(
        include_live_data=include_live_data
    )
    
    return games


@router.get("/live", response_model=List[GameResponse])
async def get_live_games(
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """
    Get currently live NHL games with real-time data.
    """
    game_service = GameService(db_session, cache)
    
    live_games = await game_service.get_live_games()
    
    return live_games


@router.post("/search", response_model=List[GameResponse])
async def search_games(
    search_request: GameSearchRequest,
    pagination: PaginationParams = Depends(),
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """
    Advanced game search with multiple criteria.
    
    Allows complex filtering including fatigue context and travel analysis.
    """
    game_service = GameService(db_session, cache)
    
    games = await game_service.search_games(
        search_request=search_request,
        offset=pagination.offset,
        limit=pagination.limit
    )
    
    return games


@router.get("/{game_id}", response_model=GameResponse)
async def get_game(
    game_id: int = Path(..., description="NHL Game ID"),
    include_live_data: bool = Query(True, description="Include live data if game is active"),
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """
    Get detailed information for a specific game.
    """
    game_service = GameService(db_session, cache)
    
    game = await game_service.get_game_by_id(
        game_id=game_id,
        include_live_data=include_live_data
    )
    
    if not game:
        raise HTTPException(
            status_code=404,
            detail=f"Game with ID {game_id} not found"
        )
    
    return game


@router.get("/{game_id}/stats", response_model=GameStatsResponse)
async def get_game_stats(
    game_id: int = Path(..., description="NHL Game ID"),
    include_events: bool = Query(False, description="Include play-by-play events"),
    include_advanced: bool = Query(True, description="Include advanced statistics"),
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """
    Get comprehensive statistics for a game.
    
    - **include_events**: Include play-by-play events (can be large)
    - **include_advanced**: Include advanced metrics like xG, Corsi
    """
    game_service = GameService(db_session, cache)
    
    stats = await game_service.get_game_stats(
        game_id=game_id,
        include_events=include_events,
        include_advanced=include_advanced
    )
    
    if not stats:
        raise HTTPException(
            status_code=404,
            detail=f"Stats not found for game {game_id}"
        )
    
    return stats


@router.get("/{game_id}/events", response_model=List[Dict[str, Any]])
async def get_game_events(
    game_id: int = Path(..., description="NHL Game ID"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    period: Optional[int] = Query(None, description="Filter by period"),
    team_id: Optional[int] = Query(None, description="Filter by team"),
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """
    Get play-by-play events for a game.
    
    - **event_type**: GOAL, SHOT, HIT, PENALTY, etc.
    - **period**: Filter events by period
    - **team_id**: Filter events by team
    """
    game_service = GameService(db_session, cache)
    
    events = await game_service.get_game_events(
        game_id=game_id,
        event_type=event_type,
        period=period,
        team_id=team_id
    )
    
    return events


@router.get("/{game_id}/fatigue-context", response_model=Dict[str, Any])
async def get_game_fatigue_context(
    game_id: int = Path(..., description="NHL Game ID"),
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """
    Get fatigue context for both teams in a game.
    
    Analyzes travel, back-to-back status, and player fatigue levels.
    """
    game_service = GameService(db_session, cache)
    
    fatigue_context = await game_service.get_fatigue_context(game_id)
    
    if not fatigue_context:
        raise HTTPException(
            status_code=404,
            detail=f"Fatigue context not available for game {game_id}"
        )
    
    return fatigue_context


@router.get("/{game_id}/prediction", response_model=GamePrediction)
async def get_game_prediction(
    game_id: int = Path(..., description="NHL Game ID"),
    model_version: Optional[str] = Query(None, description="Specific model version"),
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """
    Get AI-powered game outcome prediction.
    
    Uses machine learning models that factor in fatigue, travel, and performance.
    """
    prediction_service = GamePredictionService(db_session, cache)
    
    prediction = await prediction_service.predict_game(
        game_id=game_id,
        model_version=model_version
    )
    
    if not prediction:
        raise HTTPException(
            status_code=404,
            detail=f"Prediction not available for game {game_id}"
        )
    
    return prediction


@router.get("/{game_id}/analysis", response_model=GameAnalysis)
async def get_game_analysis(
    game_id: int = Path(..., description="NHL Game ID"),
    include_fatigue_impact: bool = Query(True, description="Include fatigue impact analysis"),
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """
    Get post-game analysis with advanced insights.
    
    Available only for completed games. Provides detailed performance analysis.
    """
    game_service = GameService(db_session, cache)
    
    analysis = await game_service.get_game_analysis(
        game_id=game_id,
        include_fatigue_impact=include_fatigue_impact
    )
    
    if not analysis:
        raise HTTPException(
            status_code=404,
            detail=f"Analysis not available for game {game_id}"
        )
    
    return analysis


@router.get("/{game_id}/three-stars", response_model=List[Dict[str, Any]])
async def get_three_stars(
    game_id: int = Path(..., description="NHL Game ID"),
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """
    Get the three stars of the game.
    
    Available only for completed games.
    """
    game_service = GameService(db_session, cache)
    
    stars = await game_service.get_three_stars(game_id)
    
    if not stars:
        raise HTTPException(
            status_code=404,
            detail=f"Three stars not available for game {game_id}"
        )
    
    return stars


@router.get("/{game_id}/momentum", response_model=Dict[str, Any])
async def get_game_momentum(
    game_id: int = Path(..., description="NHL Game ID"),
    window_minutes: int = Query(5, ge=1, le=20, description="Momentum calculation window"),
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """
    Get game momentum analysis over time.
    
    Analyzes momentum shifts based on events, shots, and possession metrics.
    """
    game_service = GameService(db_session, cache)
    
    momentum = await game_service.get_momentum_analysis(
        game_id=game_id,
        window_minutes=window_minutes
    )
    
    return momentum


@router.get("/back-to-back", response_model=List[GameResponse])
async def get_back_to_back_games(
    date_from: Optional[date] = Query(None, description="Start date"),
    date_to: Optional[date] = Query(None, description="End date"),
    team_id: Optional[int] = Query(None, description="Filter by team"),
    season: Optional[str] = SeasonParam,
    pagination: PaginationParams = Depends(),
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """
    Get games that are part of back-to-back scenarios.
    
    Useful for fatigue analysis and performance comparison.
    """
    game_service = GameService(db_session, cache)
    
    b2b_games = await game_service.get_back_to_back_games(
        date_from=date_from,
        date_to=date_to,
        team_id=team_id,
        season=season,
        offset=pagination.offset,
        limit=pagination.limit
    )
    
    return b2b_games


@router.get("/high-travel", response_model=List[GameResponse])
async def get_high_travel_games(
    min_distance: float = Query(1000.0, description="Minimum travel distance in miles"),
    date_from: Optional[date] = Query(None, description="Start date"),
    date_to: Optional[date] = Query(None, description="End date"),
    team_id: Optional[int] = Query(None, description="Filter by team"),
    pagination: PaginationParams = Depends(),
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """
    Get games involving significant travel distances.
    
    Useful for analyzing travel fatigue impact on performance.
    """
    game_service = GameService(db_session, cache)
    
    travel_games = await game_service.get_high_travel_games(
        min_distance=min_distance,
        date_from=date_from,
        date_to=date_to,
        team_id=team_id,
        offset=pagination.offset,
        limit=pagination.limit
    )
    
    return travel_games


@router.post("/{game_id}/refresh-data")
async def refresh_game_data(
    game_id: int = Path(..., description="NHL Game ID"),
    force: bool = Query(False, description="Force refresh even if recently updated"),
    db_session = Depends(get_db_session)
):
    """
    Trigger refresh of game data from NHL API.
    
    Updates live scores, events, and statistics.
    """
    game_service = GameService(db_session)
    
    result = await game_service.refresh_game_data(
        game_id=game_id,
        force=force
    )
    
    return {
        "message": f"Data refresh initiated for game {game_id}",
        "status": "success",
        "updated_at": result.get("updated_at")
    }