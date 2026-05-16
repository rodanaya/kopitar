"""
Goalie Fatigue Predictor

XGBoost-based model that predicts NHL goaltender save percentage using
fatigue-related features derived from schedule density, travel load, and
player context.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Model name used with the registry
_MODEL_NAME = "fatigue_predictor"


class GoalieFatiguePredictor:
    """XGBoost-based goalie save% prediction model using fatigue features."""

    feature_names: list[str] = [
        "composite_fatigue_index",
        "days_since_last_game",
        "miles_traveled_last_7_days",
        "timezone_changes_last_7_days",
        "games_last_7_days",
        "toi_last_7_days",
        "back_to_back_games",
        "three_in_four_nights",
        "player_age_at_game",
        "is_home_game",
        "opponent_goals_per_game",
        "altitude_change",
    ]

    def __init__(self) -> None:
        self.model = None  # XGBRegressor, set after training / loading

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    def train(self, X: pd.DataFrame, y: pd.Series) -> None:
        """
        Train an XGBRegressor on the provided features and labels.

        Args:
            X: DataFrame whose columns match ``feature_names``.
            y: Target series of save percentages (0.0 – 1.0).
        """
        try:
            from xgboost import XGBRegressor
        except ImportError as exc:
            raise ImportError("xgboost is required for training. Install it with: pip install xgboost") from exc

        self.model = XGBRegressor(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            random_state=42,
            verbosity=0,
        )
        self.model.fit(X[self.feature_names], y)
        logger.info(
            "GoalieFatiguePredictor trained on %d samples (features: %s)",
            len(X),
            self.feature_names,
        )

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------

    def predict(self, features: dict) -> float:
        """
        Predict save percentage for a single game context.

        Falls back to the analytic formula when the model has not been
        trained yet.

        Args:
            features: Mapping of feature name → value. Missing keys default
                      to 0.

        Returns:
            Predicted save percentage clamped to [0.850, 0.970].
        """
        if self.model is None:
            return self._formula_fallback(features)

        row = self._features_to_frame(features)
        prediction: float = float(self.model.predict(row)[0])
        return float(np.clip(prediction, 0.850, 0.970))

    def predict_with_confidence(
        self, features: dict
    ) -> Tuple[float, float, float]:
        """
        Return a prediction together with ±0.015 uncertainty bounds.

        Args:
            features: Same mapping accepted by :meth:`predict`.

        Returns:
            Tuple of (prediction, lower_bound, upper_bound).
        """
        prediction = self.predict(features)
        uncertainty = 0.015
        lower = float(np.clip(prediction - uncertainty, 0.850, 0.970))
        upper = float(np.clip(prediction + uncertainty, 0.850, 0.970))
        return prediction, lower, upper

    # ------------------------------------------------------------------
    # Synthetic data & model bootstrap
    # ------------------------------------------------------------------

    def generate_synthetic_training_data(
        self, n_samples: int = 500
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Generate realistic synthetic training data for bootstrapping.

        Relationships baked into the generated data:
        - save_pct ~ N(0.910, 0.025)
        - composite_fatigue_index has a negative correlation
          (~-0.002 per index point)
        - back-to-back and three-in-four nights apply additional penalties
        - home advantage adds a small positive effect

        Args:
            n_samples: Number of game rows to generate.

        Returns:
            Tuple of (feature DataFrame, save_pct Series).
        """
        rng = np.random.default_rng(seed=0)

        # --- independent features -------------------------------------------
        fatigue_idx = rng.uniform(0, 80, n_samples)
        days_rest = rng.choice([0, 1, 2, 3, 4, 5], n_samples,
                               p=[0.05, 0.15, 0.35, 0.25, 0.12, 0.08])
        miles = rng.exponential(600, n_samples).clip(0, 4000)
        tz_changes = rng.integers(0, 4, n_samples)
        games_7d = rng.integers(0, 5, n_samples)
        toi_7d = rng.uniform(0, 4000, n_samples)          # seconds
        b2b = rng.integers(0, 3, n_samples)
        t3in4 = rng.integers(0, 2, n_samples)
        age = rng.uniform(20, 40, n_samples)
        is_home = rng.integers(0, 2, n_samples)
        opp_gpg = rng.uniform(2.0, 3.8, n_samples)
        altitude_chg = rng.uniform(-5000, 5000, n_samples)

        # --- target: save percentage ----------------------------------------
        base = 0.910
        noise = rng.normal(0, 0.020, n_samples)

        save_pct = (
            base
            - fatigue_idx * 0.0002
            + np.where(days_rest >= 2, 0.004, 0.0)
            - (miles / 10000) * 0.008
            + is_home * 0.003
            - b2b * 0.003
            - t3in4 * 0.002
            - np.maximum(0, age - 35) * 0.001   # age decline after 35
            + noise
        )
        save_pct = np.clip(save_pct, 0.850, 0.970)

        X = pd.DataFrame(
            {
                "composite_fatigue_index": fatigue_idx,
                "days_since_last_game": days_rest.astype(float),
                "miles_traveled_last_7_days": miles,
                "timezone_changes_last_7_days": tz_changes.astype(float),
                "games_last_7_days": games_7d.astype(float),
                "toi_last_7_days": toi_7d,
                "back_to_back_games": b2b.astype(float),
                "three_in_four_nights": t3in4.astype(float),
                "player_age_at_game": age,
                "is_home_game": is_home.astype(float),
                "opponent_goals_per_game": opp_gpg,
                "altitude_change": altitude_chg,
            }
        )
        y = pd.Series(save_pct, name="save_pct")
        return X, y

    def load_or_create_model(self, model_path: Optional[str] = None) -> None:
        """
        Load a serialised model from *model_path* (or the registry default).
        If the file is not found, generate synthetic data and train a new model.

        Args:
            model_path: Optional explicit path to a .pkl file.  When omitted
                        the registry's MODEL_DIR / "fatigue_predictor.pkl" is
                        used.
        """
        import pickle
        from pathlib import Path as _Path

        # Resolve path
        if model_path is not None:
            pkl_path = _Path(model_path)
        else:
            from .model_registry import MODEL_DIR
            pkl_path = MODEL_DIR / f"{_MODEL_NAME}.pkl"

        if pkl_path.exists():
            try:
                with open(pkl_path, "rb") as fh:
                    self.model = pickle.load(fh)
                logger.info("Loaded existing model from %s", pkl_path)
                return
            except Exception as exc:
                logger.warning("Failed to load model from %s: %s – retraining.", pkl_path, exc)

        # Not found or unreadable → bootstrap from synthetic data
        logger.info("Model not found at %s – generating synthetic data and training.", pkl_path)
        X, y = self.generate_synthetic_training_data()
        self.train(X, y)

        # Persist for future loads
        try:
            pkl_path.parent.mkdir(parents=True, exist_ok=True)
            with open(pkl_path, "wb") as fh:
                pickle.dump(self.model, fh)
            logger.info("New model saved to %s", pkl_path)
        except OSError as exc:
            logger.warning("Could not save model to %s: %s", pkl_path, exc)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _features_to_frame(self, features: dict) -> pd.DataFrame:
        """Build a single-row DataFrame aligned to ``feature_names``."""
        row = {name: features.get(name, 0.0) for name in self.feature_names}
        return pd.DataFrame([row])

    def _formula_fallback(self, features: dict) -> float:
        """
        Analytic fallback used when no trained model is available.

        Formula (from CLAUDE.md domain spec):
            base_save_pct = 0.912
            fatigue_penalty = fatigue_index * 0.0002
            rest_bonus      = min(0.005, (days_rest - 1) * 0.002)
            travel_penalty  = (miles / 10000) * 0.008
            home_bonus      = 0.003 if is_home else 0.0
            predicted       = base - penalty + rest + travel_penalty + home
        """
        fatigue_idx = float(features.get("composite_fatigue_index", 0.0))
        days_rest = float(features.get("days_since_last_game", 1.0))
        miles = float(features.get("miles_traveled_last_7_days", 0.0))
        is_home = bool(features.get("is_home_game", False))

        base_save_pct = 0.912
        fatigue_penalty = fatigue_idx * 0.0002
        rest_bonus = min(0.005, (days_rest - 1) * 0.002)
        travel_penalty = (miles / 10000) * 0.008
        home_bonus = 0.003 if is_home else 0.0

        predicted = base_save_pct - fatigue_penalty + rest_bonus - travel_penalty + home_bonus
        return float(max(0.850, min(0.970, predicted)))
