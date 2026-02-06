"""
TCGPlayer price ingestion (optional / future work).

Status:
    - Not integrated into the main pipeline.
    - Requires TCGPlayer API credentials.
    - Kept for roadmap completeness and future extension.

This module is intentionally isolated so the core pipeline can run without it.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv
from requests.exceptions import RequestException


API_BASE = "https://api.tcgplayer.com"
DEFAULT_TIMEOUT_SECONDS = 30

logger = logging.getLogger(__name__)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"Missing required environment variable '{name}'. "
            "TCGPlayer ingestion is optional and requires API credentials."
        )
    return value


def get_access_token(session: requests.Session, public_key: str, private_key: str) -> str:
    """Authenticate and return an OAuth access token."""
    url = f"{API_BASE}/token"
    payload = {
        "grant_type": "client_credentials",
        "client_id": public_key,
        "client_secret": private_key,
    }
    resp = session.post(url, data=payload, timeout=DEFAULT_TIMEOUT_SECONDS)
    resp.raise_for_status()
    token = resp.json().get("access_token")
    if not token:
        raise ValueError("Token response did not include 'access_token'.")
    return token


def main() -> None:
    """
    Entry point for optional TCGPlayer ingestion.

    This currently validates credentials and demonstrates authentication only.
    """
    load_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    public_key = _require_env("TCGPLAYER_PUBLIC_KEY")
    private_key = _require_env("TCGPLAYER_PRIVATE_KEY")

    session = requests.Session()
    try:
        _ = get_access_token(session, public_key, private_key)
        logger.info("Authenticated with TCGPlayer (token acquired).")
        logger.info("TCGPlayer ingestion is not integrated into the main pipeline yet.")
    except (RequestException, ValueError) as e:
        logger.error("TCGPlayer ingestion failed: %s", e)
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
