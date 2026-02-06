"""
Minimal data quality checks for the MTG price pipeline.

These checks focus on *data integrity* (schema, missing values, row counts),
not model performance monitoring.

Functions return dictionaries that can be logged into run tracking.
"""

from __future__ import annotations

from typing import Any, Dict

import pandas as pd


def check_daily_dataset(path: str) -> Dict[str, Any]:
    """Basic integrity checks for the processed daily dataset."""
    df = pd.read_csv(path)

    required = {"id", "date", "usd"}
    missing_cols = sorted(required - set(df.columns))

    if missing_cols:
        return {
            "rows": len(df),
            "unique_cards": int(df["id"].nunique()) if "id" in df.columns else None,
            "missing_required_columns": missing_cols,
        }

    return {
        "rows": int(len(df)),
        "unique_cards": int(df["id"].nunique()),
        "missing_values": int(df[["id", "date", "usd"]].isna().any(axis=1).sum()),
        "non_positive_prices": int((df["usd"] <= 0).sum()),
        "duplicate_keys": int(df.duplicated(subset=["date", "id"]).sum()),
        "min_date": df["date"].min(),
        "max_date": df["date"].max(),
    }


def check_forecast_dataset(path: str, horizon_days: int) -> Dict[str, Any]:
    """Basic integrity checks for the forecast output."""
    df = pd.read_csv(path)

    required = {"id", "yhat_usd", "method"}
    missing_cols = sorted(required - set(df.columns))

    if missing_cols:
        return {
            "rows": int(len(df)),
            "missing_required_columns": missing_cols,
        }

    n_cards = int(df["id"].nunique())
    expected_rows = n_cards * int(horizon_days)

    return {
        "rows": int(len(df)),
        "unique_cards": n_cards,
        "expected_rows": expected_rows,
        "row_count_match": bool(len(df) == expected_rows),
        "missing_predictions": int(df["yhat_usd"].isna().sum()),
        "non_positive_predictions": int((df["yhat_usd"] <= 0).sum()),
        "method_breakdown": df["method"].value_counts().to_dict(),
        "min_prediction": float(df["yhat_usd"].min()),
        "max_prediction": float(df["yhat_usd"].max()),
    }
