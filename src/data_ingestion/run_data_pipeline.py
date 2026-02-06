"""
Main data ingestion pipeline entry point.

Currently supported sources:
- Scryfall (default)

Future:
- TCGPlayer
- eBay
"""

from data_ingestion.fetch_scryfall_prices import main as fetch_scryfall


def main():
    fetch_scryfall()


if __name__ == "__main__":
    main()
