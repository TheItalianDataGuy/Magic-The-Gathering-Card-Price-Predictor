import requests
import pandas as pd
from datetime import datetime
import os

# Configuration
mtg_url = 'https://api.scryfall.com/bulk-data'
data_dir = 'data/raw/'
output_file = os.path.join(data_dir, 'scryfall_data_csv')

# Get the download URL for the "default_cards" dataset
def get_url():
    response = requests.get(mtg_url)
    response.raise_for_status()
    data = response.json()

    # Loop through bulk metadata to find the default_cards JSON
    for item in data['data']:
        if item['type'] == 'default_cards':
            return item['download_uri']
    raise ValueError("Default cards data not found")

# Download the actual card data from the download URL
def fetch_card_data():
    url = get_url()
    print(f'Fetching bulk data from: {url}')
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

# Extract a subset of useful fields for modeling/logging
def extract_fields(cards_json):
    records = []
    timestamp = datetime.now().strftime('%d/%m/%Y, %H:%M:%S')

    for card in cards_json:
        # Skip cards without a USD price
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
    
    # Columns consistently
    df = pd.DataFrame(records)
    df = df[['timestamp', 'name', 'id', 'collector_number', 'set', 'rarity', 'usd']]
    return df

# Log the extracted data into a CSV file, appending if it already exists
def log(new_df):
    if os.path.exists(output_file):
        new_df.to_csv(output_file, mode='a', header=False, index=False)
    else:
        new_df.to_csv(output_file, index=False)
    print(f"Appended {len(new_df)} records to {output_file}")


# Run the complete ingestion pipeline
def main():
    cards_json = fetch_card_data()
    df = extract_fields(cards_json)

    # Safety check to prevent writing empty or None data
    if df is None or df.empty:
        print('No data to log.')
        return
    
    log(df)


if __name__ == '__main__':
    main()