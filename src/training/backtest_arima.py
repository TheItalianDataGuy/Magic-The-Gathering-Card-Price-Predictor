"""
Walk-forward backtesting of ARIMA models.
"""

import pandas as pd
import numpy as np
from statsmodels.tsa.arima.model import ARIMA
from pathlib import Path


def walk_forward_naive(series, horizon=7):
    errors = []

    for t in range(30, len(series) - horizon):
        train = series[:t]
        test = series[t:t + horizon]

        yhat = train[-1]
        errors.append(abs(test.mean() - yhat))

    return float(np.mean(errors)) if errors else None


def walk_forward_arima(series, order=(1,1,1), horizon=7):
    errors = []

    for t in range(30, len(series) - horizon):
        train = series[:t]
        test = series[t:t + horizon]

        try:
            model = ARIMA(train, order=order)
            fit = model.fit()
            forecast = fit.forecast(horizon)
            errors.append(np.mean(np.abs(test - forecast)))
        except Exception:
            continue

    return float(np.mean(errors)) if errors else None


def main():
    prices = pd.read_csv("./data/processed/daily_prices.csv", parse_dates=["date"])
    cards = pd.read_csv("./data/training/arima_cards.csv")

    results = []

    for card_id in cards["id"]:
        s = (
            prices[prices["id"] == card_id]
            .sort_values("date")["usd"]
            .values
        )

        arima_mae = walk_forward_arima(s)
        naive_mae = walk_forward_naive(s)

        results.append(
            {
                "id": card_id,
                "n_obs": len(s),
                "arima_mae": arima_mae,
                "naive_mae": naive_mae,
            }
        )


    out = pd.DataFrame(results)
    out.to_csv("./data/training/arima_results.csv", index=False)
    print("ARIMA backtesting complete")


if __name__ == "__main__":
    main()
