"""
Visual comparison of ARIMA vs naive baseline performance.
"""

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


def main():
    df = pd.read_csv("./data/training/arima_results.csv")
    df = df.dropna(subset=["arima_mae", "naive_mae"])

    plot_df = df[["arima_mae", "naive_mae"]]

    plt.figure(figsize=(8, 5))
    plot_df.boxplot()
    plt.ylabel("Mean Absolute Error (USD)")
    plt.title("ARIMA vs Naive Baseline (Walk-forward MAE)")
    plt.grid(axis="y", alpha=0.3)

    out_path = Path("./data/training/arima_vs_naive.png")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()

    print(f"Saved comparison plot to {out_path}")


if __name__ == "__main__":
    main()
