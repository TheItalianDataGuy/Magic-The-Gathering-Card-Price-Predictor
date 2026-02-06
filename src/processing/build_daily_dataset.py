"""
Build daily MTG price dataset.

Input:
- data/raw/scryfall_data.csv

Output:
- data/processed/daily_prices.csv

Logic:
- Parse timestamps
- Aggregate to daily frequency per card
- Keep latest observation per day
"""

import os
import pandas as pd
import logging


def main():
    raw_path = os.getenv("SCRYFALL_OUTPUT_FILE", "./data/raw/scryfall_data.csv")
    out_path = os.getenv("DAILY_DATASET_PATH", "./data/processed/daily_prices.csv")

    df = pd.read_csv(raw_path)

    # parse timestamp and create date
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    df = df.dropna(subset=["timestamp", "id", "usd"])

    df["date"] = df["timestamp"].dt.normalize() # type: ignore[attr-defined]

    # keep latest per day per card id
    df = df.sort_values("timestamp")
    daily = df.groupby(["date", "id"], as_index=False).tail(1)

    # select columns
    daily = daily[["date", "id", "name", "set", "rarity", "usd"]]

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    daily.to_csv(out_path, index=False)

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    logger.info(f"Wrote daily dataset: {out_path} ({len(daily)} rows)")


if __name__ == "__main__":
    main()
