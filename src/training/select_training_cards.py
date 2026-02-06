"""
Select cards with sufficient history for ARIMA training.
"""

import pandas as pd
from pathlib import Path


def main():
    in_path = "./data/processed/daily_prices.csv"
    out_path = "./data/training/arima_cards.csv"

    df = pd.read_csv(in_path, parse_dates=["date"])

    counts = (
        df.groupby("id")
        .size()
        .reset_index(name="n_obs")
        .sort_values("n_obs", ascending=False)
    )

    # Conservative threshold
    selected = counts[counts["n_obs"] >= 60].head(50)

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    selected.to_csv(out_path, index=False)

    print(f"Selected {len(selected)} cards for ARIMA training")


if __name__ == "__main__":
    main()
