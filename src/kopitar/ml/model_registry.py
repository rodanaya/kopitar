"""
Model Registry

Manages saving, loading, and listing serialized ML models on disk.
"""

import pickle
import logging
from pathlib import Path
from typing import Any, List, Optional

logger = logging.getLogger(__name__)

# Project root /models/ directory (four levels up from this file's package)
MODEL_DIR = Path(__file__).parent.parent.parent.parent / "models"


def _ensure_model_dir() -> None:
    """Create MODEL_DIR if it does not exist."""
    MODEL_DIR.mkdir(parents=True, exist_ok=True)


def save_model(model: Any, name: str) -> Path:
    """
    Serialize and save a model to disk.

    Args:
        model: Any pickle-serialisable object (e.g. an XGBRegressor).
        name:  Base name for the file (without extension).

    Returns:
        Path: Full path to the saved .pkl file.
    """
    _ensure_model_dir()
    model_path = MODEL_DIR / f"{name}.pkl"
    with open(model_path, "wb") as fh:
        pickle.dump(model, fh)
    logger.info("Model saved to %s", model_path)
    return model_path


def load_model(name: str) -> Optional[Any]:
    """
    Load a model from disk.

    Args:
        name: Base name of the model file (without extension).

    Returns:
        The deserialised model object, or None if the file does not exist.
    """
    model_path = MODEL_DIR / f"{name}.pkl"
    if not model_path.exists():
        logger.debug("Model file not found: %s", model_path)
        return None
    with open(model_path, "rb") as fh:
        model = pickle.load(fh)
    logger.info("Model loaded from %s", model_path)
    return model


def list_models() -> List[str]:
    """
    List the base names of all saved models.

    Returns:
        List of model name strings (file stems, no extension).
    """
    if not MODEL_DIR.exists():
        return []
    return [p.stem for p in MODEL_DIR.glob("*.pkl")]
