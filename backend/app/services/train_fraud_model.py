
import argparse
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split


FEATURES = ["amount", "balance_ratio", "recent_transfers"]
LABEL = "is_fraud"

MODEL_PATH = (
    Path(__file__).resolve().parents[1]
    / "ml"
    / "fraud_model.joblib"
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    args = parser.parse_args()

    data = pd.read_csv(args.data)

    required = FEATURES + [LABEL]
    missing = set(required) - set(data.columns)

    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")

    data = data[required].dropna()

    if not set(data[LABEL].unique()).issubset({0, 1}):
        raise ValueError("is_fraud must contain only 0 and 1.")

    if data[LABEL].nunique() != 2:
        raise ValueError("Dataset must contain both classes.")

    if data[LABEL].value_counts().min() < 2:
        raise ValueError("Each class needs at least two examples.")

    X = data[FEATURES].astype(float)
    y = data[LABEL].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.25,
        random_state=42,
        stratify=y,
    )

    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=10,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )

    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    fraud_index = list(model.classes_).index(1)
    probabilities = model.predict_proba(X_test)[:, fraud_index]

    print("\nClassification report:")
    print(classification_report(
        y_test, predictions, zero_division=0
    ))

    print("Confusion matrix:")
    print(confusion_matrix(y_test, predictions))

    print("ROC-AUC:", round(
        roc_auc_score(y_test, probabilities), 4
    ))

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)

    print(f"\nModel saved: {MODEL_PATH}")


if __name__ == "__main__":
    main()
