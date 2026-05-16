"""
Prediction and Model Performance Database Models

Models for storing ML predictions and tracking model performance.
"""

from sqlalchemy import (
    Column, Integer, String, Boolean, Float, ForeignKey, DateTime, Text, Enum
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
import enum

from .base import BaseModel, AuditMixin


class PredictionType(enum.Enum):
    """Prediction type enumeration."""
    PERFORMANCE = "performance"
    FATIGUE = "fatigue"
    INJURY_RISK = "injury_risk"
    SAVE_PERCENTAGE = "save_percentage"
    GOALS_AGAINST = "goals_against"
    POINTS = "points"
    SHOTS = "shots"
    TIME_ON_ICE = "time_on_ice"


class ModelType(enum.Enum):
    """Model type enumeration."""
    RANDOM_FOREST = "random_forest"
    XGBOOST = "xgboost"
    NEURAL_NETWORK = "neural_network"
    LINEAR_REGRESSION = "linear_regression"
    ENSEMBLE = "ensemble"
    BASELINE = "baseline"


class Prediction(BaseModel, AuditMixin):
    """
    Individual predictions for player performance.
    """
    
    __tablename__ = 'predictions'
    
    # Relationships
    player_id = Column(Integer, ForeignKey('players.id'), nullable=False, index=True)
    player = relationship("Player", back_populates="predictions")
    
    game_id = Column(Integer, ForeignKey('games.id'), nullable=False, index=True)
    game = relationship("Game")
    
    team_id = Column(Integer, ForeignKey('teams.id'), nullable=False, index=True)
    team = relationship("Team")
    
    # Prediction Metadata
    prediction_type = Column(Enum(PredictionType), nullable=False, index=True)
    model_type = Column(Enum(ModelType), nullable=False)
    model_version = Column(String(50), nullable=False)
    prediction_date = Column(DateTime, nullable=False, index=True)
    
    # Prediction Values
    predicted_value = Column(Float, nullable=False)
    confidence_score = Column(Float, nullable=False)  # 0-1
    
    # Confidence Intervals
    lower_bound = Column(Float, nullable=True)
    upper_bound = Column(Float, nullable=True)
    
    # Feature Importance (top features that drove this prediction)
    feature_importance = Column(JSONB, nullable=True)
    
    # Model Inputs
    input_features = Column(JSONB, nullable=False)
    fatigue_index = Column(Float, nullable=True)
    
    # Context
    home_away = Column(String(4), nullable=False)  # "home" or "away"
    opponent_team_id = Column(Integer, ForeignKey('teams.id'), nullable=False)
    
    # Game Context Features
    back_to_back = Column(Boolean, nullable=False, default=False)
    days_rest = Column(Float, nullable=False)
    travel_distance = Column(Float, nullable=True)
    timezone_change = Column(Float, nullable=False, default=0.0)
    
    # Actual Outcome (filled after game)
    actual_value = Column(Float, nullable=True)
    prediction_error = Column(Float, nullable=True)
    absolute_error = Column(Float, nullable=True)
    squared_error = Column(Float, nullable=True)
    
    # Validation
    correct_prediction = Column(Boolean, nullable=True)  # For classification
    within_confidence_interval = Column(Boolean, nullable=True)
    
    # Additional Metadata
    notes = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<Prediction(player_id={self.player_id}, type={self.prediction_type.value}, value={self.predicted_value})>"
    
    @property
    def accuracy_percentage(self):
        """Calculate prediction accuracy as percentage."""
        if self.actual_value is None or self.prediction_error is None:
            return None
        
        if self.actual_value == 0:
            return 100.0 if self.predicted_value == 0 else 0.0
        
        accuracy = (1 - abs(self.prediction_error) / abs(self.actual_value)) * 100
        return max(0.0, min(100.0, round(accuracy, 1)))
    
    @property
    def is_accurate(self):
        """Check if prediction is within reasonable accuracy (±20%)."""
        accuracy = self.accuracy_percentage
        return accuracy is not None and accuracy >= 80
    
    @property
    def confidence_category(self):
        """Categorize confidence level."""
        if self.confidence_score >= 0.9:
            return "very_high"
        elif self.confidence_score >= 0.7:
            return "high"
        elif self.confidence_score >= 0.5:
            return "moderate"
        elif self.confidence_score >= 0.3:
            return "low"
        else:
            return "very_low"
    
    def update_actual_outcome(self, actual_value):
        """
        Update prediction with actual outcome and calculate error metrics.
        
        Args:
            actual_value: The actual observed value
        """
        self.actual_value = actual_value
        self.prediction_error = self.predicted_value - actual_value
        self.absolute_error = abs(self.prediction_error)
        self.squared_error = self.prediction_error ** 2
        
        # Check if within confidence interval
        if self.lower_bound is not None and self.upper_bound is not None:
            self.within_confidence_interval = (
                self.lower_bound <= actual_value <= self.upper_bound
            )
        
        # For binary predictions
        if self.prediction_type in [PredictionType.FATIGUE, PredictionType.INJURY_RISK]:
            threshold = 0.5
            predicted_class = self.predicted_value >= threshold
            actual_class = actual_value >= threshold
            self.correct_prediction = predicted_class == actual_class


class ModelPerformance(BaseModel, AuditMixin):
    """
    Track performance metrics for different models over time.
    """
    
    __tablename__ = 'model_performance'
    
    # Model Information
    model_type = Column(Enum(ModelType), nullable=False, index=True)
    model_version = Column(String(50), nullable=False, index=True)
    prediction_type = Column(Enum(PredictionType), nullable=False, index=True)
    
    # Evaluation Period
    evaluation_start_date = Column(DateTime, nullable=False)
    evaluation_end_date = Column(DateTime, nullable=False)
    
    # Sample Size
    total_predictions = Column(Integer, nullable=False)
    valid_predictions = Column(Integer, nullable=False)  # With actual outcomes
    
    # Regression Metrics
    mean_absolute_error = Column(Float, nullable=True)
    mean_squared_error = Column(Float, nullable=True)
    root_mean_squared_error = Column(Float, nullable=True)
    r_squared = Column(Float, nullable=True)
    
    # Classification Metrics (for binary predictions)
    accuracy = Column(Float, nullable=True)
    precision = Column(Float, nullable=True)
    recall = Column(Float, nullable=True)
    f1_score = Column(Float, nullable=True)
    auc_roc = Column(Float, nullable=True)
    
    # Confidence Calibration
    confidence_calibration_score = Column(Float, nullable=True)
    predictions_in_confidence_interval = Column(Float, nullable=True)  # Percentage
    
    # Performance by Context
    home_game_performance = Column(JSONB, nullable=True)
    away_game_performance = Column(JSONB, nullable=True)
    back_to_back_performance = Column(JSONB, nullable=True)
    high_fatigue_performance = Column(JSONB, nullable=True)
    
    # Performance by Position (for player models)
    goalie_performance = Column(JSONB, nullable=True)
    forward_performance = Column(JSONB, nullable=True)
    defense_performance = Column(JSONB, nullable=True)
    
    # Trend Analysis
    performance_trend = Column(String(20), nullable=True)  # "improving", "declining", "stable"
    trend_coefficient = Column(Float, nullable=True)
    
    # Feature Importance Summary
    top_features = Column(JSONB, nullable=True)
    feature_stability = Column(Float, nullable=True)  # How stable features are over time
    
    # Comparison to Baseline
    baseline_improvement = Column(Float, nullable=True)  # % improvement over baseline
    
    # Model Diagnostics
    overfitting_score = Column(Float, nullable=True)
    drift_detection_score = Column(Float, nullable=True)
    data_quality_score = Column(Float, nullable=True)
    
    # Deployment Metrics
    prediction_latency_ms = Column(Float, nullable=True)
    memory_usage_mb = Column(Float, nullable=True)
    
    # Additional Notes
    notes = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<ModelPerformance(model={self.model_type.value}, version={self.model_version})>"
    
    @property
    def performance_grade(self):
        """Get overall performance grade."""
        if self.prediction_type.value in ["performance", "save_percentage", "points"]:
            # Use R-squared for regression
            score = self.r_squared if self.r_squared else 0
        else:
            # Use accuracy for classification
            score = self.accuracy if self.accuracy else 0
        
        if score >= 0.9:
            return "A+"
        elif score >= 0.85:
            return "A"
        elif score >= 0.8:
            return "A-"
        elif score >= 0.75:
            return "B+"
        elif score >= 0.7:
            return "B"
        elif score >= 0.65:
            return "B-"
        elif score >= 0.6:
            return "C+"
        elif score >= 0.5:
            return "C"
        else:
            return "F"
    
    @property
    def is_production_ready(self):
        """Check if model meets production quality thresholds."""
        if self.prediction_type.value in ["performance", "save_percentage", "points"]:
            return (
                self.r_squared and self.r_squared >= 0.7 and
                self.total_predictions >= 100 and
                self.data_quality_score and self.data_quality_score >= 0.8
            )
        else:
            return (
                self.accuracy and self.accuracy >= 0.75 and
                self.f1_score and self.f1_score >= 0.7 and
                self.total_predictions >= 100 and
                self.data_quality_score and self.data_quality_score >= 0.8
            )
    
    def calculate_composite_score(self):
        """Calculate composite performance score (0-100)."""
        if self.prediction_type.value in ["performance", "save_percentage", "points"]:
            primary_metric = self.r_squared or 0
        else:
            primary_metric = self.f1_score or 0
        
        # Weight different components
        score = primary_metric * 60  # 60% primary metric
        
        if self.confidence_calibration_score:
            score += self.confidence_calibration_score * 20  # 20% calibration
        
        if self.data_quality_score:
            score += self.data_quality_score * 10  # 10% data quality
        
        if self.baseline_improvement:
            score += min(10, self.baseline_improvement / 10) * 10  # 10% baseline improvement
        
        return min(100, round(score, 1))