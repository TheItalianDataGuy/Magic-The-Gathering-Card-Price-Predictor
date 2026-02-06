"""
Build the daily MTG price dataset.

Input:
    - data/raw/scryfall_data.csv (append-only raw snapshots)

Output:
    - data/processed/daily_prices.csv

Logic:
    - Parse timestamps
    - Normalize to daily frequency
    - Group by (date, card_id) and keep the latest observation per day
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

import pandas as pd


logger = logging.getLogger(__name__)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    raw_path = os.getenv("SCRYFALL_OUTPUT_FILE", "./data/raw/scryfall_data.csv")
    out_path = os.getenv("DAILY_DATASET_PATH", "./data/processed/daily_prices.csv")

    if not Path(raw_path).exists():
        raise FileNotFoundError(f"Raw dataset not found: {raw_path}. Run ingestion first.")

    df = pd.read_csv(raw_path)

    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    df = df.dropna(subset=["timestamp", "id", "usd"])

    # Normalize timestamps to day boundaries (UTC).
    df["date"] = df["timestamp"].dt.normalize()  # type: ignore[attr-defined]

    df = df.sort_values("timestamp")

    # Keep the latest observation per (date, id).
    daily = df.groupby(["date", "id"], as_index=False).tail(1)
    daily = daily[["date", "id", "name", "set", "rarity", "usd"]]

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    daily.to_csv(out_path, index=False)

    logger.info("Wrote daily dataset: %s (%s rows)", out_path, len(daily))


if __name__ == "__main__":
    main()
