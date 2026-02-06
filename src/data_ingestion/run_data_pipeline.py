"""
Pipeline entry point (happy path).

Runs:
    1) Scryfall ingestion (raw snapshots)
    2) Daily dataset build (processed)
    3) Forecast for all cards (predictions + tracking)

Recommended usage:
    python -m src.data_ingestion.run_data_pipeline
"""

from __future__ import annotations

from src.data_ingestion.fetch_scryfall_prices import main as fetch_scryfall
from src.forecasting.forecast_all_cards import main as forecast_all_cards
from src.processing.build_daily_dataset import main as build_daily_dataset


def main() -> None:
    fetch_scryfall()
    build_daily_dataset()
    forecast_all_cards()


if __name__ == "__main__":
    main()
