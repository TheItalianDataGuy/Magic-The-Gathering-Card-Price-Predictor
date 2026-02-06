"""
Pipeline entry point.

Runs the complete happy path:
1) Ingest raw prices from Scryfall (append-only)
2) Build daily dataset (processed)
3) Forecast all cards for the next 7 days
4) Write a lightweight run record (tracking)

Usage (recommended):
    python -m src.data_ingestion.run_data_pipeline
"""

from src.data_ingestion.fetch_scryfall_prices import main as fetch_scryfall
from src.processing.build_daily_dataset import main as build_daily_dataset
from src.forecasting.forecast_all_cards import main as forecast_all_cards


def main():
    fetch_scryfall()
    build_daily_dataset()
    forecast_all_cards()


if __name__ == "__main__":
    main()
