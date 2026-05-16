"""
Fatigue Analysis API Router

Specialized endpoints for fatigue analysis, workload management,
and performance impact assessment.
"""

from typing import List, Optional, Dict, Any
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Path, BackgroundTasks
from fastapi.responses import JSONResponse

from ..schemas.common import PaginationParams, SeasonParam, AnalyticsParams
from ..dependencies import get_db_session, get_cache, get_current_user
from ..services.fatigue import FatigueAnalysisService
from ..services.workload import WorkloadManagementService

router = APIRouter()


@router.get("/league-overview", response_model=Dict[str, Any])
async def get_league_fatigue_overview(
    season: Optional[str] = SeasonParam,
    position: Optional[str] = Query(None, description="Filter by position (G, D, F)"),
    include_trends: bool = Query(True, description="Include trend analysis"),
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """
    Get league-wide fatigue metrics and trends.
    
    Provides comprehensive overview of fatigue patterns across the NHL.
    """
    fatigue_service = FatigueAnalysisService(db_session, cache)
    
    overview = await fatigue_service.get_league_fatigue_overview(
        season=season,
        position=position,
        include_trends=include_trends
    )
    
    return overview


@router.get("/hotspots", response_model=List[Dict[str, Any]])
async def get_fatigue_hotspots(
    season: Optional[str] = SeasonParam,
    threshold: float = Query(70.0, description="Fatigue threshold for hotspot detection"),
    time_window: int = Query(14, description="Analysis window in days"),
    include_predictions: bool = Query(True, description="Include fatigue predictions"),
    pagination: PaginationParams = Depends(),
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """
    Identify current fatigue hotspots across the league.
    
    Returns players and teams with high fatigue levels requiring attention.
    """
    fatigue_service = FatigueAnalysisService(db_session, cache)
    
    hotspots = await fatigue_service.identify_fatigue_hotspots(
        season=season,
        threshold=threshold,
        time_window=time_window,
        include_predictions=include_predictions,
        offset=pagination.offset,
        limit=pagination.limit
    )
    
    return hotspots


@router.get("/performance-correlation", response_model=Dict[str, Any])
async def get_fatigue_performance_correlation(
    season: Optional[str] = SeasonParam,
    position: Optional[str] = Query(None, description="Filter by position"),
    metrics: List[str] = Query(
        ["goals", "assists", "save_percentage", "plus_minus"],
        description="Performance metrics to correlate"
    ),
    correlation_method: str = Query("pearson", description="Correlation method"),
    min_games: int = Query(10, description="Minimum games for inclusion"),
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """
    Analyze correlation between fatigue and performance metrics.
    
    Quantifies how fatigue impacts various performance indicators.
    """
    fatigue_service = FatigueAnalysisService(db_session, cache)
    
    correlation = await fatigue_service.analyze_performance_correlation(
        season=season,
        position=position,
        metrics=metrics,
        correlation_method=correlation_method,
        min_games=min_games
    )
    
    return correlation


@router.get("/workload-distribution", response_model=Dict[str, Any])
async def get_workload_distribution(
    season: Optional[str] = SeasonParam,
    team_id: Optional[int] = Query(None, description="Filter by team"),
    position: Optional[str] = Query(None, description="Filter by position"),
    aggregation_level: str = Query("team", description="Aggregation level (player, team, league)"),
    include_recommendations: bool = Query(True, description="Include workload recommendations"),
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """
    Analyze workload distribution across players and teams.
    
    Identifies workload imbalances and optimization opportunities.
    """
    workload_service = WorkloadManagementService(db_session, cache)
    
    distribution = await workload_service.analyze_workload_distribution(
        season=season,
        team_id=team_id,
        position=position,
        aggregation_level=aggregation_level,
        include_recommendations=include_recommendations
    )
    
    return distribution


@router.get("/recovery-patterns", response_model=Dict[str, Any])
async def get_recovery_patterns(
    season: Optional[str] = SeasonParam,
    position: Optional[str] = Query(None, description="Filter by position"),
    age_group: Optional[str] = Query(None, description="Age group filter (young, prime, veteran)"),
    min_rest_days: int = Query(1, description="Minimum rest days to analyze"),
    include_individual: bool = Query(False, description="Include individual player patterns"),
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """
    Analyze player recovery patterns after fatigue.
    
    Studies how different player types recover from high workload periods.
    """
    fatigue_service = FatigueAnalysisService(db_session, cache)
    
    patterns = await fatigue_service.analyze_recovery_patterns(
        season=season,
        position=position,
        age_group=age_group,
        min_rest_days=min_rest_days,
        include_individual=include_individual
    )
    
    return patterns


@router.get("/travel-fatigue", response_model=Dict[str, Any])
async def get_travel_fatigue_analysis(
    season: Optional[str] = SeasonParam,
    min_distance: float = Query(1000.0, description="Minimum travel distance"),
    include_timezone: bool = Query(True, description="Include timezone change analysis"),
    team_id: Optional[int] = Query(None, description="Filter by team"),
    time_window: int = Query(7, description="Post-travel analysis window in days"),
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """
    Analyze fatigue specifically related to travel.
    
    Focuses on travel distance and timezone change impacts on fatigue.
    """
    fatigue_service = FatigueAnalysisService(db_session, cache)
    
    travel_fatigue = await fatigue_service.analyze_travel_fatigue(
        season=season,
        min_distance=min_distance,
        include_timezone=include_timezone,
        team_id=team_id,
        time_window=time_window
    )
    
    return travel_fatigue


@router.get("/schedule-impact", response_model=Dict[str, Any])
async def get_schedule_fatigue_impact(
    season: Optional[str] = SeasonParam,
    team_id: Optional[int] = Query(None, description="Filter by team"),
    scenario_type: str = Query("back_to_back", description="Schedule scenario type"),
    include_predictions: bool = Query(True, description="Include future impact predictions"),
    comparison_baseline: str = Query("regular", description="Baseline for comparison"),
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """
    Analyze fatigue impact of different schedule scenarios.
    
    Compares performance in challenging schedule situations vs. normal games.
    """
    fatigue_service = FatigueAnalysisService(db_session, cache)
    
    schedule_impact = await fatigue_service.analyze_schedule_impact(
        season=season,
        team_id=team_id,
        scenario_type=scenario_type,
        include_predictions=include_predictions,
        comparison_baseline=comparison_baseline
    )
    
    return schedule_impact


@router.get("/player/{player_id}/history", response_model=Dict[str, Any])
async def get_player_fatigue_history(
    player_id: int = Path(..., description="Player ID"),
    season: Optional[str] = SeasonParam,
    window_days: int = Query(10, description="Analysis window size"),
    include_context: bool = Query(True, description="Include game context"),
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """
    Get detailed fatigue history for a specific player.
    
    Tracks fatigue patterns over time with game context.
    """
    fatigue_service = FatigueAnalysisService(db_session, cache)
    
    history = await fatigue_service.get_player_fatigue_history(
        player_id=player_id,
        season=season,
        window_days=window_days,
        include_context=include_context
    )
    
    if not history:
        raise HTTPException(
            status_code=404,
            detail=f"Fatigue history not found for player {player_id}"
        )
    
    return history


@router.get("/team/{team_id}/management", response_model=Dict[str, Any])
async def get_team_fatigue_management(
    team_id: int = Path(..., description="Team ID"),
    season: Optional[str] = SeasonParam,
    include_recommendations: bool = Query(True, description="Include management recommendations"),
    forecast_days: int = Query(14, description="Forecast period in days"),
    position_breakdown: bool = Query(True, description="Break down by position"),
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """
    Get comprehensive team fatigue management analysis.
    
    Provides actionable insights for coaching staff and management.
    """
    workload_service = WorkloadManagementService(db_session, cache)
    
    management_info = await workload_service.get_team_management_analysis(
        team_id=team_id,
        season=season,
        include_recommendations=include_recommendations,
        forecast_days=forecast_days,
        position_breakdown=position_breakdown
    )
    
    return management_info


@router.get("/optimal-rest", response_model=Dict[str, Any])
async def get_optimal_rest_recommendations(
    team_id: Optional[int] = Query(None, description="Filter by team"),
    position: Optional[str] = Query(None, description="Filter by position"),
    current_fatigue_threshold: float = Query(60.0, description="Current fatigue threshold"),
    optimization_horizon: int = Query(21, description="Optimization horizon in days"),
    constraints: List[str] = Query([], description="Rest constraints"),
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """
    Generate optimal rest recommendations using ML optimization.
    
    Balances performance maintenance with fatigue management.
    """
    workload_service = WorkloadManagementService(db_session, cache)
    
    recommendations = await workload_service.generate_rest_recommendations(
        team_id=team_id,
        position=position,
        current_fatigue_threshold=current_fatigue_threshold,
        optimization_horizon=optimization_horizon,
        constraints=constraints
    )
    
    return recommendations


@router.get("/risk-assessment", response_model=Dict[str, Any])
async def get_fatigue_risk_assessment(
    season: Optional[str] = SeasonParam,
    team_id: Optional[int] = Query(None, description="Filter by team"),
    position: Optional[str] = Query(None, description="Filter by position"),
    risk_categories: List[str] = Query(
        ["injury", "performance_decline", "burnout"],
        description="Risk categories to assess"
    ),
    time_horizon: int = Query(14, description="Risk assessment horizon in days"),
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """
    Assess various risks associated with current fatigue levels.
    
    Evaluates injury risk, performance decline, and burnout probability.
    """
    fatigue_service = FatigueAnalysisService(db_session, cache)
    
    risk_assessment = await fatigue_service.assess_fatigue_risks(
        season=season,
        team_id=team_id,
        position=position,
        risk_categories=risk_categories,
        time_horizon=time_horizon
    )
    
    return risk_assessment


@router.post("/calculate-custom", response_model=Dict[str, Any])
async def calculate_custom_fatigue_metrics(
    player_ids: List[int] = Query(..., description="Player IDs to analyze"),
    weight_config: Dict[str, float] = {},
    analysis_date: Optional[date] = Query(None, description="Analysis date"),
    window_days: int = Query(10, description="Analysis window"),
    include_breakdown: bool = Query(True, description="Include factor breakdown"),
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """
    Calculate fatigue metrics with custom weighting.
    
    Allows customization of fatigue calculation parameters.
    """
    fatigue_service = FatigueAnalysisService(db_session, cache)
    
    custom_metrics = await fatigue_service.calculate_custom_fatigue(
        player_ids=player_ids,
        weight_config=weight_config,
        analysis_date=analysis_date,
        window_days=window_days,
        include_breakdown=include_breakdown
    )
    
    return custom_metrics


@router.post("/trigger-analysis", response_model=Dict[str, Any])
async def trigger_fatigue_analysis_update(
    background_tasks: BackgroundTasks,
    analysis_type: str = Query("daily", description="Analysis type to trigger"),
    force_refresh: bool = Query(False, description="Force refresh of cached data"),
    current_user = Depends(get_current_user),
    db_session = Depends(get_db_session)
):
    """
    Trigger background fatigue analysis update.
    
    Requires authentication and runs analysis asynchronously.
    """
    fatigue_service = FatigueAnalysisService(db_session)
    
    # Add background task
    background_tasks.add_task(
        fatigue_service.run_analysis_update,
        analysis_type=analysis_type,
        force_refresh=force_refresh,
        user_id=current_user.id
    )
    
    return {
        "message": f"Fatigue analysis update initiated: {analysis_type}",
        "status": "queued",
        "analysis_type": analysis_type
    }


@router.get("/benchmarks", response_model=Dict[str, Any])
async def get_fatigue_benchmarks(
    position: str = Query(..., description="Position for benchmarks (G, D, F)"),
    season: Optional[str] = SeasonParam,
    percentiles: List[float] = Query(
        [25.0, 50.0, 75.0, 90.0, 95.0],
        description="Percentiles to calculate"
    ),
    age_adjusted: bool = Query(True, description="Adjust benchmarks for age"),
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """
    Get fatigue benchmarks for position comparison.
    
    Provides percentile-based benchmarks for evaluating player fatigue levels.
    """
    fatigue_service = FatigueAnalysisService(db_session, cache)
    
    benchmarks = await fatigue_service.get_fatigue_benchmarks(
        position=position,
        season=season,
        percentiles=percentiles,
        age_adjusted=age_adjusted
    )
    
    return benchmarks