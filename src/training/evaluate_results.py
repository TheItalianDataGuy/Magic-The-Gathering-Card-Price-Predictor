"""
Compare ARIMA performance against naive baseline.
"""

import pandas as pd


def main():
    df = pd.read_csv("./data/training/arima_results.csv")

    summary = {
        "cards_tested": len(df),
        "mean_mae": df["arima_mae"].mean(),
        "median_mae": df["arima_mae"].median(),
    }

    print("ARIMA evaluation summary")
    for k, v in summary.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()
