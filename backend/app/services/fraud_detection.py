
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.transaction import Transaction
from app.services.ml_fraud_model import predict_fraud_probability


def calculate_fraud_assessment(
    amount: Decimal,
    current_balance: Decimal,
    sender_account_id: int,
    db: Session,
) -> dict:
    """Combine existing risk rules with an optional ML model."""

    score = 0.0
    risk_factors = []

    # Rule 1: Transaction amount
    if amount >= Decimal("50000"):
        score += 50
        risk_factors.append(
            "Very large transaction amount (Rs. 50,000 or more)"
        )
    elif amount >= Decimal("10000"):
        score += 30
        risk_factors.append(
            "Large transaction amount (Rs. 10,000 or more)"
        )
    elif amount >= Decimal("5000"):
        score += 15
        risk_factors.append(
            "Elevated transaction amount (Rs. 5,000 or more)"
        )

    # Rule 2: Balance utilization
    balance_ratio = 0.0

    if current_balance > 0:
        balance_ratio = float(amount / current_balance)

        if balance_ratio >= 0.90:
            score += 40
            risk_factors.append(
                "Transaction uses at least 90% of current balance"
            )
        elif balance_ratio >= 0.70:
            score += 25
            risk_factors.append(
                "Transaction uses at least 70% of current balance"
            )
        elif balance_ratio >= 0.50:
            score += 10
            risk_factors.append(
                "Transaction uses at least 50% of current balance"
            )

    # Rule 3: Recent transfer frequency
    time_limit = datetime.now(timezone.utc) - timedelta(minutes=5)

    recent_transfers = (
        db.query(Transaction)
        .filter(
            Transaction.sender_account_id == sender_account_id,
            Transaction.transaction_type == "TRANSFER",
            Transaction.created_at >= time_limit,
        )
        .count()
    )

    if recent_transfers >= 5:
        score += 40
        risk_factors.append(
            "Five or more transfers detected in the last five minutes"
        )
    elif recent_transfers >= 3:
        score += 20
        risk_factors.append(
            "Three or more transfers detected in the last five minutes"
        )
    elif recent_transfers >= 1:
        score += 10
        risk_factors.append(
            "Recent transfer activity detected in the last five minutes"
        )

    rule_score = min(score, 100.0)

    # ML prediction is optional until the model is trained.
    ml_probability = predict_fraud_probability(
        amount=float(amount),
        balance_ratio=balance_ratio,
        recent_transfers=recent_transfers,
    )

    if ml_probability is not None:
        ml_score = ml_probability * 100.0

        # Hybrid score: 60% rules, 40% ML.
        score = 0.60 * rule_score + 0.40 * ml_score
        detection_method = "HYBRID_ML_AND_RULES"

        risk_factors.append(
            f"ML-estimated fraud probability: {ml_score:.1f}%"
        )
    else:
        score = rule_score
        detection_method = "RULE_BASED"

        risk_factors.append(
            "ML model unavailable; rule-based assessment used"
        )

    score = round(min(max(score, 0.0), 100.0), 2)

    if not risk_factors:
        risk_factors.append(
            "No configured risk indicators were triggered"
        )

    return {
        "fraud_score": score,
        "risk_level": get_risk_level(score),
        "risk_factors": risk_factors,
        "rule_based_score": round(rule_score, 2),
        "ml_fraud_probability": ml_probability,
        "detection_method": detection_method,
    }


def calculate_fraud_score(
    amount: Decimal,
    current_balance: Decimal,
    sender_account_id: int,
    db: Session,
) -> float:
    """Maintain compatibility with existing callers."""

    return calculate_fraud_assessment(
        amount,
        current_balance,
        sender_account_id,
        db,
    )["fraud_score"]


def get_risk_level(score: float) -> str:
    if score >= 70:
        return "HIGH"
    elif score >= 30:
        return "MEDIUM"
    return "LOW"
