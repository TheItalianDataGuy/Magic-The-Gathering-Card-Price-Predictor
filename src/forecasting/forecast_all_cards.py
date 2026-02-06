"""
Forecast all MTG cards for the next N days (default: 7).

Input:
    - data/processed/daily_prices.csv

Output:
    - data/predictions/forecast_7d.csv

Method (robust baselines, per card):
    - < 7 observations   -> naive last value
    - 7–13 observations  -> 7-day moving average (flat)
    - >= 14 observations -> EWMA span=7 (flat)

Notes:
    - Designed to run for ALL cards without crashing on short histories.
    - Output integrity is validated via data-quality checks.
"""

from __future__ import annotations

import logging
import os
import uuid
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

from src.monitoring.data_quality import check_forecast_dataset
from src.utils.tracking import log_metrics, log_run_metadata


logger = logging.getLogger(__name__)


def ewma_last(y: np.ndarray, span: int = 7) -> float:
    s = pd.Series(y)
    return float(s.ewm(span=span, adjust=False).mean().iloc[-1])


def moving_average_last(y: np.ndarray, window: int = 7) -> float:
    w = min(window, len(y))
    return float(np.mean(y[-w:]))


def _choose_baseline(y: np.ndarray) -> tuple[float, str]:
    n_obs = len(y)

    if n_obs >= 14:
        return ewma_last(y, span=7), "ewma_7"
    if n_obs >= 7:
        return moving_average_last(y, window=7), "ma_7"
    return float(y[-1]), "naive_last"


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    run_id = f"forecast_{pd.Timestamp.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

    in_path = os.getenv("DAILY_DATASET_PATH", "./data/processed/daily_prices.csv")
    out_path = os.getenv("FORECAST_7D_PATH", "./data/predictions/forecast_7d.csv")
    horizon_days = int(os.getenv("FORECAST_HORIZON_DAYS", "7"))

    if not Path(in_path).exists():
        raise FileNotFoundError(f"Daily dataset not found: {in_path}. Run build_daily_dataset.py first.")

    df = pd.read_csv(in_path)
    df["date"] = pd.to_datetime(df["date"], utc=True, errors="coerce")
    df = df.dropna(subset=["date", "id", "usd"])
    df = df.sort_values(["id", "date"])

    run_ts = pd.Timestamp.utcnow().isoformat()
    n_cards = int(df["id"].nunique())
    logger.info("Loaded daily dataset: %s rows, %s unique cards", len(df), n_cards)

    rows: List[Dict] = []

    for card_id, g in df.groupby("id", sort=False):
        g = g.sort_values("date")

        name = g["name"].iloc[-1] if "name" in g.columns else ""
        set_code = g["set"].iloc[-1] if "set" in g.columns else ""
        rarity = g["rarity"].iloc[-1] if "rarity" in g.columns else ""

        y = g["usd"].astype(float).to_numpy()
        last_date = g["date"].iloc[-1]
        n_obs = len(y)

        yhat, method = _choose_baseline(y)

        # Guard against invalid values.
        if (not np.isfinite(yhat)) or (yhat <= 0):
            yhat, method = float(y[-1]), "naive_fallback"

        for h in range(1, horizon_days + 1):
            f_date = (last_date + pd.Timedelta(days=h)).date()
            rows.append(
                {
                    "run_id": run_id,
                    "run_timestamp": run_ts,
                    "id": card_id,
                    "name": name,
                    "set": set_code,
                    "rarity": rarity,
                    "last_date": str(last_date.date()),
                    "forecast_date": str(f_date),
                    "yhat_usd": round(float(yhat), 4),
                    "method": method,
                    "n_obs": n_obs,
                }
            )

    out_df = pd.DataFrame(rows)

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(out_path, index=False)

    forecast_quality = check_forecast_dataset(out_path, horizon_days)
    method_counts = out_df["method"].value_counts().to_dict()

    log_run_metadata(
        run_id,
        {
            "step": "forecast_all_cards",
            "horizon_days": horizon_days,
            "input_path": in_path,
            "output_path": out_path,
            "n_cards": n_cards,
        },
    )

    log_metrics(
        run_id,
        {
            "n_forecast_rows": int(len(out_df)),
            "method_breakdown": method_counts,
            "forecast_data_quality": forecast_quality,
        },
    )

    logger.info("Wrote forecasts: %s (%s rows)", out_path, len(out_df))


if __name__ == "__main__":
    main()
