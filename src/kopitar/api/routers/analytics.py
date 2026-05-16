"""
Analytics API Router

Endpoints for advanced analytics, reports, and data insights
across players, teams, and league-wide patterns.
"""

from typing import List, Optional, Dict, Any
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from fastapi.responses import JSONResponse

from ..schemas.common import PaginationParams, SeasonParam, AnalyticsParams
from ..dependencies import get_db_session, get_cache, get_current_user
from ..services.analytics import AnalyticsService
from ..services.reports import ReportService

router = APIRouter()


@router.get("/league-overview", response_model=Dict[str, Any])
async def get_league_overview(
    season: Optional[str] = SeasonParam,
    include_trends: bool = Query(True, description="Include trend analysis"),
    include_fatigue: bool = Query(True, description="Include fatigue metrics"),
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """
    Get comprehensive league-wide analytics overview.
    
    Provides high-level insights across all teams and players.
    """
    analytics_service = AnalyticsService(db_session, cache)
    
    overview = await analytics_service.get_league_overview(
        season=season,
        include_trends=include_trends,
        include_fatigue=include_fatigue
    )
    
    return overview


@router.get("/fatigue-trends", response_model=Dict[str, Any])
async def get_fatigue_trends(
    season: Optional[str] = SeasonParam,
    position: Optional[str] = Query(None, description="Filter by position (G, D, F)"),
    team_id: Optional[int] = Query(None, description="Filter by team"),
    time_period: str = Query("season", description="Analysis period (week, month, season)"),
    analytics_params: AnalyticsParams = Depends(),
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """
    Analyze league-wide fatigue trends and patterns.
    
    Identifies fatigue hotspots and performance correlations.
    """
    analytics_service = AnalyticsService(db_session, cache)
    
    fatigue_trends = await analytics_service.get_fatigue_trends(
        season=season,
        position=position,
        team_id=team_id,
        time_period=time_period,
        analytics_params=analytics_params
    )
    
    return fatigue_trends


@router.get("/travel-impact", response_model=Dict[str, Any])
async def get_travel_impact_analysis(
    season: Optional[str] = SeasonParam,
    min_distance: float = Query(500.0, description="Minimum travel distance"),
    include_timezone: bool = Query(True, description="Include timezone analysis"),
    aggregation_level: str = Query("team", description="Aggregation level (player, team, league)"),
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """
    Analyze the impact of travel on team and player performance.
    
    Correlates travel distance, timezone changes with performance metrics.
    """
    analytics_service = AnalyticsService(db_session, cache)
    
    travel_analysis = await analytics_service.analyze_travel_impact(
        season=season,
        min_distance=min_distance,
        include_timezone=include_timezone,
        aggregation_level=aggregation_level
    )
    
    return travel_analysis


@router.get("/back-to-back-performance", response_model=Dict[str, Any])
async def get_back_to_back_performance(
    season: Optional[str] = SeasonParam,
    position: Optional[str] = Query(None, description="Filter by position"),
    team_id: Optional[int] = Query(None, description="Filter by team"),
    include_individual: bool = Query(False, description="Include individual player analysis"),
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """
    Analyze performance in back-to-back game scenarios.
    
    Compares B2B performance vs. regular games across various metrics.
    """
    analytics_service = AnalyticsService(db_session, cache)
    
    b2b_analysis = await analytics_service.analyze_back_to_back_performance(
        season=season,
        position=position,
        team_id=team_id,
        include_individual=include_individual
    )
    
    return b2b_analysis


@router.get("/schedule-strength", response_model=Dict[str, Any])
async def get_schedule_strength_analysis(
    season: Optional[str] = SeasonParam,
    team_id: Optional[int] = Query(None, description="Filter by specific team"),
    include_fatigue_factor: bool = Query(True, description="Include fatigue in strength calculation"),
    future_window_days: int = Query(30, description="Days ahead to analyze"),
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """
    Analyze schedule strength and difficulty across teams.
    
    Factors in opponent strength, travel, and fatigue accumulation.
    """
    analytics_service = AnalyticsService(db_session, cache)
    
    schedule_analysis = await analytics_service.analyze_schedule_strength(
        season=season,
        team_id=team_id,
        include_fatigue_factor=include_fatigue_factor,
        future_window_days=future_window_days
    )
    
    return schedule_analysis


@router.get("/advanced-metrics-correlation", response_model=Dict[str, Any])
async def get_advanced_metrics_correlation(
    season: Optional[str] = SeasonParam,
    metrics: List[str] = Query(
        ["fatigue_index", "corsi_for_percentage", "expected_goals_for", "pdo"],
        description="Metrics to correlate"
    ),
    position: Optional[str] = Query(None, description="Filter by position"),
    min_games: int = Query(20, description="Minimum games threshold"),
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """
    Analyze correlations between advanced metrics and fatigue.
    
    Identifies which advanced stats are most affected by fatigue factors.
    """
    analytics_service = AnalyticsService(db_session, cache)
    
    correlation_analysis = await analytics_service.analyze_metrics_correlation(
        season=season,
        metrics=metrics,
        position=position,
        min_games=min_games
    )
    
    return correlation_analysis


@router.get("/performance-predictions", response_model=Dict[str, Any])
async def get_performance_predictions(
    prediction_type: str = Query("team_performance", description="Type of prediction"),
    horizon_days: int = Query(7, ge=1, le=30, description="Prediction horizon"),
    team_id: Optional[int] = Query(None, description="Specific team prediction"),
    player_id: Optional[int] = Query(None, description="Specific player prediction"),
    confidence_threshold: float = Query(0.7, description="Minimum confidence level"),
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """
    Get machine learning-based performance predictions.
    
    Predicts various performance metrics based on fatigue and context factors.
    """
    analytics_service = AnalyticsService(db_session, cache)
    
    predictions = await analytics_service.get_performance_predictions(
        prediction_type=prediction_type,
        horizon_days=horizon_days,
        team_id=team_id,
        player_id=player_id,
        confidence_threshold=confidence_threshold
    )
    
    return predictions


@router.get("/era-comparison", response_model=Dict[str, Any])
async def get_era_comparison(
    era1_seasons: List[str] = Query(..., description="First era seasons"),
    era2_seasons: List[str] = Query(..., description="Second era seasons"),
    metrics: List[str] = Query(
        ["goals_per_game", "save_percentage", "power_play_percentage"],
        description="Metrics to compare"
    ),
    normalize_schedule: bool = Query(True, description="Normalize for schedule differences"),
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """
    Compare hockey metrics across different eras.
    
    Accounts for rule changes, schedule differences, and playing styles.
    """
    analytics_service = AnalyticsService(db_session, cache)
    
    era_comparison = await analytics_service.compare_eras(
        era1_seasons=era1_seasons,
        era2_seasons=era2_seasons,
        metrics=metrics,
        normalize_schedule=normalize_schedule
    )
    
    return era_comparison


@router.get("/injury-risk-analysis", response_model=Dict[str, Any])
async def get_injury_risk_analysis(
    season: Optional[str] = SeasonParam,
    position: Optional[str] = Query(None, description="Filter by position"),
    team_id: Optional[int] = Query(None, description="Filter by team"),
    risk_threshold: str = Query("medium", description="Risk threshold (low, medium, high)"),
    include_predictions: bool = Query(True, description="Include risk predictions"),
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """
    Analyze injury risk factors and patterns.
    
    Correlates fatigue, workload, and travel with historical injury data.
    """
    analytics_service = AnalyticsService(db_session, cache)
    
    injury_analysis = await analytics_service.analyze_injury_risk(
        season=season,
        position=position,
        team_id=team_id,
        risk_threshold=risk_threshold,
        include_predictions=include_predictions
    )
    
    return injury_analysis


@router.get("/optimal-rotation", response_model=Dict[str, Any])
async def get_optimal_rotation_analysis(
    team_id: int = Query(..., description="Team ID for rotation analysis"),
    position: str = Query(..., description="Position to analyze (G, D, F)"),
    season: Optional[str] = SeasonParam,
    optimization_target: str = Query("performance", description="Optimization target"),
    constraints: List[str] = Query([], description="Rotation constraints"),
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """
    Analyze optimal player rotation strategies.
    
    Uses optimization algorithms to balance performance and fatigue management.
    """
    analytics_service = AnalyticsService(db_session, cache)
    
    rotation_analysis = await analytics_service.analyze_optimal_rotation(
        team_id=team_id,
        position=position,
        season=season,
        optimization_target=optimization_target,
        constraints=constraints
    )
    
    return rotation_analysis


@router.post("/generate-report", response_model=Dict[str, Any])
async def generate_custom_report(
    report_type: str = Query(..., description="Type of report to generate"),
    parameters: Dict[str, Any] = {},
    format: str = Query("json", description="Report format (json, pdf, csv)"),
    current_user = Depends(get_current_user),
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """
    Generate custom analytics reports.
    
    Requires authentication and supports various output formats.
    """
    report_service = ReportService(db_session, cache)
    
    report = await report_service.generate_report(
        report_type=report_type,
        parameters=parameters,
        format=format,
        user_id=current_user.id
    )
    
    return {
        "report_id": report.id,
        "status": "generated",
        "download_url": report.download_url,
        "expires_at": report.expires_at
    }


@router.get("/model-performance", response_model=Dict[str, Any])
async def get_model_performance_metrics(
    model_type: Optional[str] = Query(None, description="Filter by model type"),
    time_period: str = Query("30d", description="Performance period"),
    include_accuracy: bool = Query(True, description="Include accuracy metrics"),
    current_user = Depends(get_current_user),
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """
    Get performance metrics for ML models.
    
    Tracks model accuracy, drift, and prediction quality over time.
    """
    analytics_service = AnalyticsService(db_session, cache)
    
    model_performance = await analytics_service.get_model_performance(
        model_type=model_type,
        time_period=time_period,
        include_accuracy=include_accuracy
    )
    
    return model_performance


@router.get("/data-quality", response_model=Dict[str, Any])
async def get_data_quality_metrics(
    data_source: Optional[str] = Query(None, description="Filter by data source"),
    time_period: str = Query("7d", description="Quality check period"),
    include_completeness: bool = Query(True, description="Include completeness metrics"),
    current_user = Depends(get_current_user),
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """
    Get data quality and completeness metrics.
    
    Monitors data pipeline health and identifies quality issues.
    """
    analytics_service = AnalyticsService(db_session, cache)
    
    quality_metrics = await analytics_service.get_data_quality_metrics(
        data_source=data_source,
        time_period=time_period,
        include_completeness=include_completeness
    )
    
    return quality_metrics