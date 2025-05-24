import os
import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
import logging
from requests.exceptions import RequestException

load_dotenv()

API_BASE = "https://api.tcgplayer.com"
PUBLIC_KEY = os.getenv("TCGPLAYER_PUBLIC_KEY")
PRIVATE_KEY = os.getenv("TCGPLAYER_PRIVATE_KEY")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

def get_output_path():
    """
    Get the output file path for saving price data CSV.
    Reads environment variable 'TCGPLAYER_OUTPUT_FILE' or returns default.
    
    Returns:
        str: Path to the CSV output file.
    """
    return os.getenv("TCGPLAYER_OUTPUT_FILE", "data/raw/tcgplayer_prices.csv")

def get_bearer_token():
    """
    Authenticate with TCGPlayer API using client credentials flow 
    and retrieve an OAuth2 Bearer token.

    Returns:
        str or None: Access token string if successful, None otherwise.
    """
    url = f"{API_BASE}/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "client_credentials",
        "client_id": PUBLIC_KEY,
        "client_secret": PRIVATE_KEY
    }
    try:
        resp = requests.post(url, headers=headers, data=data, timeout=10)
        resp.raise_for_status()
        token = resp.json().get("access_token")
        if not token:
            logger.error("Failed to get bearer token: no access_token in response")
        return token
    except RequestException as e:
        logger.error(f"RequestException in get_bearer_token: {e}")
        return None

def search_products(card_name: str, token: str):
    """
    Search TCGPlayer product catalog for cards matching the given name.

    Args:
        card_name (str): The name of the Magic card to search for.
        token (str): Valid OAuth2 bearer token.

    Returns:
        list: A list of product dictionaries matching the search.
    """
    url = f"{API_BASE}/catalog/products"
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "productName": card_name,
        "productTypes": "Cards",
        "limit": 100
    }
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json().get("results", [])
    except RequestException as e:
        logger.error(f"RequestException in search_products({card_name}): {e}")
        return []

def get_set_name(group_id: int, token: str) -> str:
    """
    Retrieve the human-readable set name from a TCGPlayer group ID.

    Args:
        group_id (int): The group (set) ID.
        token (str): Valid OAuth2 bearer token.

    Returns:
        str: Set name if found, else empty string.
    """
    url = f"{API_BASE}/catalog/groups/{group_id}"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        results = resp.json().get("results", [])
        if not results:
            logger.warning(f"No set name found for group_id={group_id}")
            return ""
        return results[0].get("name", "")
    except RequestException as e:
        logger.error(f"RequestException in get_set_name({group_id}): {e}")
        return ""
    except ValueError as e:
        logger.error(f"JSON decode error in get_set_name({group_id}): {e}")
        return ""

def fetch_price(product_id: int, token: str) -> dict:
    """
    Fetch current pricing details for a product by its product ID.

    Args:
        product_id (int): TCGPlayer product ID.
        token (str): Valid OAuth2 bearer token.

    Returns:
        dict: Pricing information dictionary (lowPrice, midPrice, etc.) or empty dict if none found.
    """
    url = f"{API_BASE}/pricing/product/{product_id}"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        results = resp.json().get("results", [])
        if not results:
            logger.warning(f"No pricing data found for product_id={product_id}")
            return {}
        return results[0]
    except RequestException as e:
        logger.error(f"RequestException in fetch_price({product_id}): {e}")
        return {}

def extract_records(cards_and_sets: list) -> pd.DataFrame:
    """
    For each (card_name, set_name), search TCGPlayer catalog, find matching product,
    fetch current prices, and collect records in a DataFrame.

    Args:
        cards_and_sets (list): List of tuples (card_name, set_name).

    Returns:
        pd.DataFrame: DataFrame with columns:
            timestamp, card_name, set_name, product_id,
            low_price, mid_price, high_price, market_price, direct_low
    """
    token = get_bearer_token()
    if not token:
        logger.error("No bearer token, aborting fetch.")
        return pd.DataFrame()

    records = []

    for card_name, set_name in cards_and_sets:
        candidates = search_products(card_name, token)
        if not candidates:
            logger.warning(f"No candidates found for card {card_name}")
            continue

        for prod in candidates:
            group_name = get_set_name(prod.get("groupId"), token)
            if group_name.lower() == set_name.lower():
                price_info = fetch_price(prod.get("productId"), token)
                if price_info:
                    records.append({
                        "timestamp": datetime.utcnow().isoformat(),
                        "card_name": card_name,
                        "set_name": set_name,
                        "product_id": prod.get("productId"),
                        "low_price": price_info.get("lowPrice"),
                        "mid_price": price_info.get("midPrice"),
                        "high_price": price_info.get("highPrice"),
                        "market_price": price_info.get("marketPrice"),
                        "direct_low": price_info.get("directLowPrice"),
                    })
                else:
                    logger.warning(f"No price info for product {prod.get('productId')}")
                break
        else:
            logger.warning(f"No matching set found for card {card_name} in set {set_name}")

    return pd.DataFrame(records)

def log(df: pd.DataFrame):
    """
    Append records DataFrame to CSV file, creating it if it doesn't exist.

    Args:
        df (pd.DataFrame): DataFrame to save.
    """
    out_path = get_output_path()
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    if df.empty:
        logger.info("No records to save.")
        return

    if os.path.exists(out_path):
        df.to_csv(out_path, mode="a", header=False, index=False)
    else:
        df.to_csv(out_path, index=False)

    logger.info(f"Appended {len(df)} records to {out_path}")

def main():
    """
    Example main function to fetch and log prices for sample cards.
    """
    cards_and_sets = [
        ("Sheoldred, the Apocalypse", "Dominaria United"),
        ("Ragavan, Nimble Pilferer", "Modern Horizons 2"),
    ]

    df = extract_records(cards_and_sets)
    log(df)

if __name__ == "__main__":
    main()
