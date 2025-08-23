# src/pooling.py

import pandas as pd
from config import BUYERS_DB_PATH, EXPORTER_SCORE_WEIGHTS

def load_buyers():
    """Load and return buyers/exporters database as DataFrame."""
    return pd.read_csv(BUYERS_DB_PATH)

def score_exporter(pool, buyer_row):
    """Score a buyer/exporter for pool matching."""
    # Add more sophisticated logic here as needed!
    score = (
        EXPORTER_SCORE_WEIGHTS["price"] * (buyer_row["price_per_kg"] / 3500) +
        EXPORTER_SCORE_WEIGHTS["payment_speed"] * (20 - buyer_row["payment_days"]) / 20 +  # Scaled so lower days are better
        EXPORTER_SCORE_WEIGHTS["reputation"] * (buyer_row["reputation"] / 100) +
        EXPORTER_SCORE_WEIGHTS["logistics_support"] * (1 if buyer_row["logistics_support"] == "Yes" else 0)
    )
    return round(score, 2)

def recommend_exporters(pool):
    """Return sorted list of (exporter, score) for given pool."""
    buyers = load_buyers()
    buyers["score"] = buyers.apply(lambda row: score_exporter(pool, row), axis=1)
    return buyers.sort_values("score", ascending=False)
