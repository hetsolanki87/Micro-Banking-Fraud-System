
from pathlib import Path

import numpy as np
import pandas as pd


# Reproducible data for academic development only.
rng = np.random.default_rng(42)

NUMBER_OF_TRANSACTIONS = 5000

# Generate a mix of small, medium and large transactions.
amount = rng.lognormal(
    mean=7.5,
    sigma=1.1,
    size=NUMBER_OF_TRANSACTIONS,
)
amount = np.clip(amount, 50, 100000).round(2)

# Fraction of the available balance being transferred.
balance_ratio = rng.beta(
    1.5, 4.0, size=NUMBER_OF_TRANSACTIONS
)

# Number of recent transfers in a five-minute window.
recent_transfers = np.clip(
    rng.poisson(1.2, size=NUMBER_OF_TRANSACTIONS),
    0,
    8,
)

# Simulated probability model used ONLY to create synthetic labels.
# These labels are not real fraud findings.
logit = (
    -4.5
    + amount / 25000
    + 2.0 * balance_ratio
    + 0.55 * recent_transfers
)

probability = 1.0 / (1.0 + np.exp(-logit))
is_fraud = rng.binomial(1, probability)

data = pd.DataFrame({
    "amount": amount,
    "balance_ratio": balance_ratio.round(4),
    "recent_transfers": recent_transfers,
    "is_fraud": is_fraud,
})

output_path = (
    Path(__file__).resolve().parent
    / "fraud_training_data.csv"
)

data.to_csv(output_path, index=False)

print("Synthetic dataset created successfully.")
print(f"Saved to: {output_path}")
print(f"Total transactions: {len(data)}")
print("\nLabel counts:")
print(data["is_fraud"].value_counts().sort_index())
print("\nFraud proportion:")
print(f"{data['is_fraud'].mean():.2%}")
print("\nFirst five rows:")
print(data.head().to_string(index=False))
