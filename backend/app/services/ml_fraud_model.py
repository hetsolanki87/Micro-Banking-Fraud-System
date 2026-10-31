
from pathlib import Path
import logging

import joblib

logger = logging.getLogger(__name__)

MODEL_PATH = (
    Path(__file__).resolve().parents[1]
    / "ml"
    / "fraud_model.joblib"
)


def predict_fraud_probability(
    amount: float,
    balance_ratio: float,
    recent_transfers: int,
) -> float | None:
    """Return predicted fraud probability between 0 and 1."""

    if not MODEL_PATH.exists():
        return None

    try:
        model = joblib.load(MODEL_PATH)

        features = [[
            amount,
            balance_ratio,
            recent_transfers,
        ]]

        probabilities = model.predict_proba(features)[0]
        classes = list(model.classes_)

        if 1 not in classes:
            raise ValueError(
                "Model must be trained with fraud label 1."
            )

        return float(probabilities[classes.index(1)])

    except Exception:
        logger.exception("Fraud ML prediction failed")
        raise
