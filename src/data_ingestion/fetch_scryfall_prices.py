import requests
import pandas as pd
from datetime import datetime
import os

# Configuration
mtg_url = 'https://api.scryfall.com/bulk-data'
data_dir = 'data/raw/'
output_file = os.path.join(data_dir, 'scryfall_data_csv')

def get_url():
    """
    Retrieve the download URI for the 'default_cards' bulk data set from the Scryfall API.

    Makes a GET request to the bulk data endpoint, parses the JSON response to find
    the 'default_cards' type, and returns its download URI.

    Returns:
        str: URL to download the default_cards JSON bulk data.

    Raises:
        ValueError: If the 'default_cards' data type is not found in the bulk data response.
        requests.HTTPError: If the GET request to the bulk data endpoint fails.
    """
    response = requests.get(mtg_url)
    response.raise_for_status()
    data = response.json()

    for item in data['data']:
        if item['type'] == 'default_cards':
            return item['download_uri']
    raise ValueError("Default cards data not found")

def fetch_card_data():
    """
    Download the full bulk JSON card data from Scryfall.

    Calls `get_url()` to get the current download URL for default_cards bulk data,
    then performs a GET request to fetch the full JSON data.

    Returns:
        list: List of card dictionaries from the bulk data JSON.

    Raises:
        requests.HTTPError: If the GET request to download the bulk data fails.
    """
    url = get_url()
    print(f'Fetching bulk data from: {url}')
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def extract_fields(cards_json):
    """
    Extract a subset of useful fields from the raw card JSON data.

    Iterates over each card dictionary, filters out cards without a USD price,
    and collects selected fields (name, id, set, rarity, collector number, price)
    with a timestamp.

    Args:
        cards_json (list): List of card dictionaries.

    Returns:
        pandas.DataFrame: DataFrame with columns:
            ['timestamp', 'name', 'id', 'collector_number', 'set', 'rarity', 'usd']
    """
    records = []
    timestamp = datetime.now().strftime('%d/%m/%Y, %H:%M:%S')

    for card in cards_json:
        usd_price = card.get('prices', {}).get('usd')
        if usd_price is not None:
            records.append(
                {
                    'timestamp': timestamp,
                    'name': card['name'],
                    'id': card['id'],
                    'collector_number': card['collector_number'],
                    'set': card['set'],
                    'rarity': card['rarity'],
                    'usd': float(usd_price)
                }
            )
    
    df = pd.DataFrame(records)
    # Ensure consistent column order
    df = df[['timestamp', 'name', 'id', 'collector_number', 'set', 'rarity', 'usd']]
    return df

def log(new_df):
    """
    Append or create the CSV file to store the extracted card data.

    Uses environment variable 'OUTPUT_FILE' for file path if set,
    otherwise defaults to '/opt/airflow/data/raw/scryfall_data.csv'.

    Creates the directory if it does not exist.
    Appends without header if the file exists; otherwise creates a new file.

    Args:
        new_df (pandas.DataFrame): DataFrame of new records to log.
    """
    output_file = os.getenv("OUTPUT_FILE", "/opt/airflow/data/raw/scryfall_data.csv")

    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    if os.path.exists(output_file):
        new_df.to_csv(output_file, mode='a', header=False, index=False)
    else:
        new_df.to_csv(output_file, index=False)

    print(f"Appended {len(new_df)} records to {output_file}")

def main():
    """
    Main ingestion pipeline function.

    Fetches the full bulk card data JSON, extracts relevant fields into a DataFrame,
    performs a safety check to ensure data is present,
    and logs the data to CSV file.
    """
    cards_json = fetch_card_data()
    df = extract_fields(cards_json)

    if df is None or df.empty:
        print('No data to log.')
        return
    
    log(df)

if __name__ == '__main__':
    main()
