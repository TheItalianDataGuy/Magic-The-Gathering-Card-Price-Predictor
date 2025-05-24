import os
import logging
import requests
import pandas as pd
from datetime import datetime
from requests.exceptions import RequestException

# Configure logging for clear debug/info/error messages
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration URL for bulk data metadata
mtg_url = 'https://api.scryfall.com/bulk-data'

def get_url():
    """
    Retrieve the download URL for the 'default_cards' bulk data JSON from Scryfall.

    Makes a GET request to the Scryfall bulk data endpoint and searches for
    the 'default_cards' type to obtain the current download URI.

    Returns:
        str: URL pointing to the bulk JSON data for default cards.

    Raises:
        RequestException: If the HTTP request fails.
        ValueError: If 'default_cards' data is not found in the response.
    """
    try:
        response = requests.get(mtg_url, timeout=10)
        response.raise_for_status()
        data = response.json()
        for item in data['data']:
            if item['type'] == 'default_cards':
                logger.info(f"Found default_cards download URL: {item['download_uri']}")
                return item['download_uri']
        raise ValueError("Default cards data not found")
    except RequestException as e:
        logger.error(f"Failed to get bulk data URL: {e}")
        raise

def fetch_card_data():
    """
    Download the full bulk card data JSON from Scryfall.

    Calls get_url() to retrieve the download URL, then performs
    a GET request to download the complete bulk data.

    Returns:
        list: List of card dictionaries parsed from JSON.

    Raises:
        RequestException: If the HTTP request fails.
    """
    try:
        url = get_url()
        logger.info(f"Fetching bulk data from: {url}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.json()
    except RequestException as e:
        logger.error(f"Failed to fetch bulk card data: {e}")
        raise

def extract_fields(cards_json):
    """
    Extract selected fields from the raw Scryfall card JSON data.

    Filters cards that have a USD price, and constructs a list of
    dictionaries with relevant fields plus a timestamp.

    Args:
        cards_json (list): List of card dictionaries from Scryfall bulk data.

    Returns:
        pandas.DataFrame: DataFrame containing timestamp, name, id,
                          collector_number, set, rarity, and USD price.
    """
    records = []
    timestamp = datetime.now().strftime('%d/%m/%Y, %H:%M:%S')

    for card in cards_json:
        usd_price = card.get('prices', {}).get('usd')
        if usd_price is not None:
            records.append({
                'timestamp': timestamp,
                'name': card['name'],
                'id': card['id'],
                'collector_number': card['collector_number'],
                'set': card['set'],
                'rarity': card['rarity'],
                'usd': float(usd_price)
            })

    df = pd.DataFrame(records)
    df = df[['timestamp', 'name', 'id', 'collector_number', 'set', 'rarity', 'usd']]
    logger.info(f"Extracted {len(df)} records with USD prices.")
    return df

def log(new_df):
    """
    Append or create a CSV file to save extracted card data.

    Uses the SCRYFALL_OUTPUT_FILE environment variable if set; otherwise
    defaults to '/opt/airflow/data/raw/scryfall_data.csv'.

    Creates the directory path if it does not exist.

    Args:
        new_df (pandas.DataFrame): DataFrame containing card records to save.
    """
    output_file = os.getenv("SCRYFALL_OUTPUT_FILE", "/opt/airflow/data/raw/scryfall_data.csv")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    if os.path.exists(output_file):
        new_df.to_csv(output_file, mode='a', header=False, index=False)
        logger.info(f"Appended {len(new_df)} records to existing file: {output_file}")
    else:
        new_df.to_csv(output_file, index=False)
        logger.info(f"Created new file and wrote {len(new_df)} records: {output_file}")

def main():
    """
    Run the full ingestion pipeline:
    - Fetch bulk card data from Scryfall
    - Extract relevant fields for modeling
    - Log data to CSV file with appropriate logging and error handling
    """
    try:
        cards_json = fetch_card_data()
        df = extract_fields(cards_json)

        if df.empty:
            logger.warning("No data to log.")
            return

        log(df)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")

if __name__ == '__main__':
    main()
