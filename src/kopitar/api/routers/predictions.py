"""
Predictions API Router

Endpoints for machine learning-based predictions including
performance forecasting, game outcomes, and fatigue projections.
"""

from typing import List, Optional, Dict, Any
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Path, BackgroundTasks
from fastapi.responses import JSONResponse

from ..schemas.common import PaginationParams, SeasonParam
from ..dependencies import get_db_session, get_cache, get_current_user
from ..services.predictions import PredictionService
from ..services.ml_models import MLModelService

router = APIRouter()


@router.get("/player/{player_id}/performance", response_model=Dict[str, Any])
async def predict_player_performance(
    player_id: int = Path(..., description="Player ID"),
    prediction_date: Optional[date] = Query(None, description="Prediction target date"),
    horizon_days: int = Query(7, ge=1, le=30, description="Prediction horizon"),
    metrics: List[str] = Query(
        ["goals", "assists", "points", "shots"],
        description="Metrics to predict"
    ),
    model_version: Optional[str] = Query(None, description="Specific model version"),
    include_confidence: bool = Query(True, description="Include confidence intervals"),
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """
    Predict future performance metrics for a specific player.
    
    Uses ML models that factor in fatigue, recent performance, and context.
    """
    prediction_service = PredictionService(db_session, cache)
    
    predictions = await prediction_service.predict_player_performance(
        player_id=player_id,
        prediction_date=prediction_date,
        horizon_days=horizon_days,
        metrics=metrics,
        model_version=model_version,
        include_confidence=include_confidence
    )
    
    if not predictions:
        raise HTTPException(
            status_code=404,
            detail=f"Performance predictions not available for player {player_id}"
        )
    
    return predictions


@router.get("/team/{team_id}/performance", response_model=Dict[str, Any])
async def predict_team_performance(
    team_id: int = Path(..., description="Team ID"),
    prediction_date: Optional[date] = Query(None, description="Prediction target date"),
    horizon_days: int = Query(14, ge=1, le=30, description="Prediction horizon"),
    metrics: List[str] = Query(
        ["goals_for", "goals_against", "win_probability"],
        description="Team metrics to predict"
    ),
    include_player_breakdown: bool = Query(False, description="Include player-level breakdown"),
    model_version: Optional[str] = Query(None, description="Specific model version"),
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """
    Predict future performance metrics for a team.
    
    Aggregates individual player predictions and team-level factors.
    """
    prediction_service = PredictionService(db_session, cache)
    
    predictions = await prediction_service.predict_team_performance(
        team_id=team_id,
        prediction_date=prediction_date,
        horizon_days=horizon_days,
        metrics=metrics,
        include_player_breakdown=include_player_breakdown,
        model_version=model_version
    )
    
    if not predictions:
        raise HTTPException(
            status_code=404,
            detail=f"Performance predictions not available for team {team_id}"
        )
    
    return predictions


@router.get("/game/{game_id}/outcome", response_model=Dict[str, Any])
async def predict_game_outcome(
    game_id: int = Path(..., description="Game ID"),
    include_player_impact: bool = Query(True, description="Include player fatigue impact"),
    include_travel_impact: bool = Query(True, description="Include travel fatigue impact"),
    model_ensemble: bool = Query(True, description="Use ensemble of models"),
    confidence_threshold: float = Query(0.6, description="Minimum confidence for prediction"),
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """
    Predict the outcome of a specific game.
    
    Considers team form, player fatigue, travel, and historical matchups.
    """
    prediction_service = PredictionService(db_session, cache)
    
    prediction = await prediction_service.predict_game_outcome(
        game_id=game_id,
        include_player_impact=include_player_impact,
        include_travel_impact=include_travel_impact,
        model_ensemble=model_ensemble,
        confidence_threshold=confidence_threshold
    )
    
    if not prediction:
        raise HTTPException(
            status_code=404,
            detail=f"Game outcome prediction not available for game {game_id}"
        )
    
    return prediction


@router.get("/fatigue/{player_id}/forecast", response_model=Dict[str, Any])
async def predict_fatigue_levels(
    player_id: int = Path(..., description="Player ID"),
    forecast_days: int = Query(14, ge=3, le=60, description="Forecast period"),
    include_schedule: bool = Query(True, description="Include upcoming schedule impact"),
    scenario_analysis: bool = Query(False, description="Include scenario analysis"),
    model_version: Optional[str] = Query(None, description="Specific model version"),
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """
    Predict future fatigue levels for a player.
    
    Projects fatigue based on upcoming schedule and historical patterns.
    """
    prediction_service = PredictionService(db_session, cache)
    
    fatigue_forecast = await prediction_service.predict_fatigue_levels(
        player_id=player_id,
        forecast_days=forecast_days,
        include_schedule=include_schedule,
        scenario_analysis=scenario_analysis,
        model_version=model_version
    )
    
    if not fatigue_forecast:
        raise HTTPException(
            status_code=404,
            detail=f"Fatigue forecast not available for player {player_id}"
        )
    
    return fatigue_forecast


@router.get("/injury-risk/{player_id}", response_model=Dict[str, Any])
async def predict_injury_risk(
    player_id: int = Path(..., description="Player ID"),
    risk_horizon: int = Query(30, ge=7, le=90, description="Risk assessment horizon"),
    risk_factors: List[str] = Query(
        ["fatigue", "workload", "age", "injury_history"],
        description="Risk factors to include"
    ),
    include_prevention: bool = Query(True, description="Include prevention recommendations"),
    model_version: Optional[str] = Query(None, description="Specific model version"),
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """
    Predict injury risk for a specific player.
    
    Uses ML models trained on historical injury data and risk factors.
    """
    prediction_service = PredictionService(db_session, cache)
    
    risk_prediction = await prediction_service.predict_injury_risk(
        player_id=player_id,
        risk_horizon=risk_horizon,
        risk_factors=risk_factors,
        include_prevention=include_prevention,
        model_version=model_version
    )
    
    if not risk_prediction:
        raise HTTPException(
            status_code=404,
            detail=f"Injury risk prediction not available for player {player_id}"
        )
    
    return risk_prediction


@router.get("/season-projections/{team_id}", response_model=Dict[str, Any])
async def predict_season_projections(
    team_id: int = Path(..., description="Team ID"),
    season: Optional[str] = SeasonParam,
    projection_type: str = Query("playoff_probability", description="Type of projection"),
    include_scenarios: bool = Query(True, description="Include scenario analysis"),
    update_frequency: str = Query("daily", description="Projection update frequency"),
    confidence_levels: List[float] = Query([0.5, 0.8, 0.95], description="Confidence levels"),
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """
    Generate season-long projections for a team.
    
    Projects playoff probability, standings, and key milestones.
    """
    prediction_service = PredictionService(db_session, cache)
    
    projections = await prediction_service.predict_season_projections(
        team_id=team_id,
        season=season,
        projection_type=projection_type,
        include_scenarios=include_scenarios,
        update_frequency=update_frequency,
        confidence_levels=confidence_levels
    )
    
    return projections


@router.get("/upcoming-games", response_model=List[Dict[str, Any]])
async def predict_upcoming_games(
    date_from: Optional[date] = Query(None, description="Start date"),
    date_to: Optional[date] = Query(None, description="End date"),
    team_id: Optional[int] = Query(None, description="Filter by team"),
    min_confidence: float = Query(0.6, description="Minimum prediction confidence"),
    include_betting_odds: bool = Query(False, description="Include betting implications"),
    pagination: PaginationParams = Depends(),
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """
    Get predictions for upcoming games.
    
    Provides batch predictions for multiple games with filtering options.
    """
    prediction_service = PredictionService(db_session, cache)
    
    game_predictions = await prediction_service.predict_upcoming_games(
        date_from=date_from,
        date_to=date_to,
        team_id=team_id,
        min_confidence=min_confidence,
        include_betting_odds=include_betting_odds,
        offset=pagination.offset,
        limit=pagination.limit
    )
    
    return game_predictions


@router.get("/model-accuracy", response_model=Dict[str, Any])
async def get_prediction_accuracy(
    model_type: Optional[str] = Query(None, description="Filter by model type"),
    time_period: str = Query("30d", description="Accuracy measurement period"),
    prediction_category: Optional[str] = Query(None, description="Prediction category"),
    include_drift_analysis: bool = Query(False, description="Include model drift analysis"),
    current_user = Depends(get_current_user),
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """
    Get accuracy metrics for prediction models.
    
    Tracks model performance and identifies areas for improvement.
    """
    ml_service = MLModelService(db_session, cache)
    
    accuracy_metrics = await ml_service.get_model_accuracy(
        model_type=model_type,
        time_period=time_period,
        prediction_category=prediction_category,
        include_drift_analysis=include_drift_analysis
    )
    
    return accuracy_metrics


@router.post("/retrain-model", response_model=Dict[str, Any])
async def trigger_model_retraining(
    background_tasks: BackgroundTasks,
    model_type: str = Query(..., description="Model type to retrain"),
    training_data_window: str = Query("2_seasons", description="Training data window"),
    hyperparameter_tuning: bool = Query(True, description="Perform hyperparameter tuning"),
    validation_split: float = Query(0.2, description="Validation data split"),
    current_user = Depends(get_current_user),
    db_session = Depends(get_db_session)
):
    """
    Trigger model retraining with updated data.
    
    Requires authentication and runs training asynchronously.
    """
    ml_service = MLModelService(db_session)
    
    # Add background task for model retraining
    background_tasks.add_task(
        ml_service.retrain_model,
        model_type=model_type,
        training_data_window=training_data_window,
        hyperparameter_tuning=hyperparameter_tuning,
        validation_split=validation_split,
        user_id=current_user.id
    )
    
    return {
        "message": f"Model retraining initiated: {model_type}",
        "status": "queued",
        "model_type": model_type,
        "estimated_completion": "2-6 hours"
    }


@router.get("/feature-importance", response_model=Dict[str, Any])
async def get_feature_importance(
    model_type: str = Query(..., description="Model type to analyze"),
    prediction_category: Optional[str] = Query(None, description="Prediction category"),
    top_n_features: int = Query(20, description="Number of top features to return"),
    include_shap_values: bool = Query(False, description="Include SHAP values"),
    current_user = Depends(get_current_user),
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """
    Get feature importance analysis for ML models.
    
    Identifies which factors most influence predictions.
    """
    ml_service = MLModelService(db_session, cache)
    
    feature_importance = await ml_service.get_feature_importance(
        model_type=model_type,
        prediction_category=prediction_category,
        top_n_features=top_n_features,
        include_shap_values=include_shap_values
    )
    
    return feature_importance


@router.post("/custom-prediction", response_model=Dict[str, Any])
async def generate_custom_prediction(
    prediction_config: Dict[str, Any] = {},
    feature_overrides: Dict[str, float] = {},
    model_type: Optional[str] = Query(None, description="Model type to use"),
    include_explanation: bool = Query(True, description="Include prediction explanation"),
    current_user = Depends(get_current_user),
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """
    Generate custom predictions with specified parameters.
    
    Allows for hypothetical scenarios and what-if analysis.
    """
    prediction_service = PredictionService(db_session, cache)
    
    custom_prediction = await prediction_service.generate_custom_prediction(
        prediction_config=prediction_config,
        feature_overrides=feature_overrides,
        model_type=model_type,
        include_explanation=include_explanation,
        user_id=current_user.id
    )
    
    return custom_prediction


@router.get("/prediction-history/{entity_id}", response_model=List[Dict[str, Any]])
async def get_prediction_history(
    entity_id: int = Path(..., description="Entity ID (player, team, or game)"),
    entity_type: str = Query(..., description="Entity type (player, team, game)"),
    prediction_type: Optional[str] = Query(None, description="Filter by prediction type"),
    days_back: int = Query(30, description="Days of history to retrieve"),
    include_accuracy: bool = Query(True, description="Include actual vs predicted comparison"),
    pagination: PaginationParams = Depends(),
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """
    Get historical predictions for an entity.
    
    Tracks prediction accuracy and trends over time.
    """
    prediction_service = PredictionService(db_session, cache)
    
    history = await prediction_service.get_prediction_history(
        entity_id=entity_id,
        entity_type=entity_type,
        prediction_type=prediction_type,
        days_back=days_back,
        include_accuracy=include_accuracy,
        offset=pagination.offset,
        limit=pagination.limit
    )
    
    return history