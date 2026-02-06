"""
Minimal data quality checks for MTG price pipeline.

This module performs basic validation and summary checks on:
- daily processed prices
- forecast outputs

Results are logged and returned as dictionaries for tracking.
"""

import pandas as pd


def check_daily_dataset(path: str) -> dict:
    df = pd.read_csv(path)

    issues = {
        "rows": len(df),
        "unique_cards": df["id"].nunique(),
        "missing_values": int(df[["id", "date", "usd"]].isna().any(axis=1).sum()),
        "non_positive_prices": int((df["usd"] <= 0).sum()),
        "duplicate_keys": int(df.duplicated(subset=["date", "id"]).sum()),
        "min_date": df["date"].min(),
        "max_date": df["date"].max(),
    }

    return issues


def check_forecast_dataset(path: str, horizon_days: int) -> dict:
    df = pd.read_csv(path)

    n_cards = df["id"].nunique()

    issues = {
        "rows": len(df),
        "unique_cards": n_cards,
        "expected_rows": n_cards * horizon_days,
        "row_count_match": len(df) == n_cards * horizon_days,
        "missing_predictions": int(df["yhat_usd"].isna().sum()),
        "non_positive_predictions": int((df["yhat_usd"] <= 0).sum()),
        "method_breakdown": df["method"].value_counts().to_dict(),
        "min_prediction": float(df["yhat_usd"].min()),
        "max_prediction": float(df["yhat_usd"].max()),
    }

    return issues
