"""
Scryfall price ingestion.

Downloads Scryfall's bulk *default_cards* dataset and extracts a compact table
of card prices (USD) for downstream processing.

Output (append-only):
    data/raw/scryfall_data.csv

Columns:
    timestamp,name,id,collector_number,set,rarity,usd
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import requests
from dotenv import load_dotenv
from requests.exceptions import RequestException


BULK_ENDPOINT = "https://api.scryfall.com/bulk-data"
DEFAULT_TIMEOUT_SECONDS = 30

logger = logging.getLogger(__name__)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_default_cards_download_url(session: requests.Session) -> str:
    """Return the current download URL for Scryfall's 'default_cards' bulk dataset."""
    resp = session.get(BULK_ENDPOINT, timeout=DEFAULT_TIMEOUT_SECONDS)
    resp.raise_for_status()
    payload = resp.json()

    for item in payload.get("data", []):
        if item.get("type") == "default_cards":
            url = item.get("download_uri")
            if url:
                logger.info("Found default_cards download URL.")
                return url

    raise ValueError("Could not find 'default_cards' download URI in Scryfall bulk-data response.")


def download_default_cards(session: requests.Session, url: str) -> List[Dict[str, Any]]:
    """Download and parse the default_cards JSON payload."""
    resp = session.get(url, timeout=DEFAULT_TIMEOUT_SECONDS)
    resp.raise_for_status()
    data = resp.json()
    if not isinstance(data, list):
        raise ValueError("Unexpected Scryfall payload: expected a list of card objects.")
    return data


def extract_usd_prices(cards: List[Dict[str, Any]], timestamp: str) -> pd.DataFrame:
    """Extract a compact dataframe of USD prices from Scryfall card objects."""
    rows: List[Dict[str, Any]] = []

    for c in cards:
        prices = c.get("prices") or {}
        usd = prices.get("usd")
        if usd in (None, ""):
            continue

        rows.append(
            {
                "timestamp": timestamp,
                "name": c.get("name", ""),
                "id": c.get("id", ""),
                "collector_number": c.get("collector_number", ""),
                "set": c.get("set", ""),
                "rarity": c.get("rarity", ""),
                "usd": usd,
            }
        )

    df = pd.DataFrame(rows)

    if not df.empty:
        df["usd"] = pd.to_numeric(df["usd"], errors="coerce")
        df = df.dropna(subset=["usd", "id"])

    return df


def main() -> None:
    """Fetch and append the latest USD prices to the raw CSV dataset."""
    load_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    out_path = os.getenv("SCRYFALL_OUTPUT_FILE", "./data/raw/scryfall_data.csv")
    out_file = Path(out_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    timestamp = _utc_now_iso()

    session = requests.Session()
    try:
        url = get_default_cards_download_url(session)
        cards = download_default_cards(session, url)
        df = extract_usd_prices(cards, timestamp)

        if df.empty:
            logger.warning("No USD prices found in Scryfall payload.")
            return

        write_header = not out_file.exists()
        df.to_csv(out_file, mode="a", index=False, header=write_header)

        logger.info("Appended %s rows to %s", len(df), out_file)

    except (RequestException, ValueError) as e:
        logger.error("Scryfall ingestion failed: %s", e)
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
