"""
Forecast all MTG cards for the next 7 days.

Input:
- data/processed/daily_prices.csv

Output:
- data/predictions/forecast_7d.csv

Method (robust baseline, per card):
- If >= 14 observations: EWMA forecast (flat) + optional small drift
- If 7-13 observations: moving average (flat)
- If < 7 observations: naive last value

This is designed to always run for ALL cards without crashing.
"""

import os
import logging

import numpy as np
import pandas as pd
from src.utils.tracking import log_run_metadata, log_metrics
from src.monitoring.data_quality import check_forecast_dataset



logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def ewma_forecast(y: np.ndarray, span: int = 7) -> float:
    """Return the last EWMA value as a flat forecast baseline."""
    s = pd.Series(y)
    return float(s.ewm(span=span, adjust=False).mean().iloc[-1])


def moving_average_forecast(y: np.ndarray, window: int = 7) -> float:
    """Return the mean of the last `window` points (or all if shorter)."""
    w = min(window, len(y))
    return float(np.mean(y[-w:]))


def main():
    import uuid
    run_id = f"forecast_{pd.Timestamp.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

    in_path = os.getenv("DAILY_DATASET_PATH", "./data/processed/daily_prices.csv")
    out_path = os.getenv("FORECAST_7D_PATH", "./data/predictions/forecast_7d.csv")

    horizon_days = int(os.getenv("FORECAST_HORIZON_DAYS", "7"))

    if not os.path.exists(in_path):
        raise FileNotFoundError(f"Daily dataset not found: {in_path}. Run build_daily_dataset.py first.")

    df = pd.read_csv(in_path)

    # Ensure types
    df["date"] = pd.to_datetime(df["date"], utc=True, errors="coerce")
    df = df.dropna(subset=["date", "id", "usd"])

    # Sort for safety
    df = df.sort_values(["id", "date"])

    run_ts = pd.Timestamp.utcnow().isoformat()

    forecasts = []
    n_cards = df["id"].nunique()
    logger.info(f"Loaded daily dataset: {len(df)} rows, {n_cards} unique cards")

    # Group by card id
    for card_id, g in df.groupby("id", sort=False):
        g = g.sort_values("date")

        # Use last known metadata (name/set/rarity might shift; we store last seen)
        name = g["name"].iloc[-1] if "name" in g.columns else ""
        set_code = g["set"].iloc[-1] if "set" in g.columns else ""
        rarity = g["rarity"].iloc[-1] if "rarity" in g.columns else ""

        y = g["usd"].astype(float).to_numpy()
        last_date = g["date"].iloc[-1]

        n_obs = len(y)

        if n_obs >= 14:
            yhat = ewma_forecast(y, span=7)
            method = "ewma_7"
        elif n_obs >= 7:
            yhat = moving_average_forecast(y, window=7)
            method = "ma_7"
        else:
            yhat = float(y[-1])
            method = "naive_last"

        # Simple guard
        if not np.isfinite(yhat) or yhat <= 0:
            yhat = float(y[-1])
            method = "naive_fallback"

        # Emit one row per forecast day
        for h in range(1, horizon_days + 1):
            f_date = (last_date + pd.Timedelta(days=h)).date()  # output as date (YYYY-MM-DD)
            forecasts.append(
                {
                    "run_id": run_id,
                    "run_timestamp": run_ts,
                    "id": card_id,
                    "name": name,
                    "set": set_code,
                    "rarity": rarity,
                    "last_date": str(last_date.date()),
                    "forecast_date": str(f_date),
                    "yhat_usd": round(yhat, 4),
                    "method": method,
                    "n_obs": n_obs,
                }
            )

    out_df = pd.DataFrame(forecasts)

    # Write forecasts first (so monitoring can read the output file)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    out_df.to_csv(out_path, index=False)

    # Monitoring: validate forecast output
    forecast_quality = check_forecast_dataset(out_path, horizon_days)

    # Tracking metrics
    method_counts = out_df["method"].value_counts().to_dict()

    log_run_metadata(
        run_id,
        {
            "horizon_days": horizon_days,
            "input_path": in_path,
            "output_path": out_path,
            "n_cards": n_cards,
        },
    )

    log_metrics(
        run_id,
        {
            "n_forecast_rows": len(out_df),
            "method_breakdown": method_counts,
            "forecast_data_quality": forecast_quality,
        },
    )

    logger.info(f"Wrote forecasts: {out_path} ({len(out_df)} rows)")
    logger.info("Done.")



if __name__ == "__main__":
    main()
