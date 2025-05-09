import requests
from curl_cffi.requests import get
import pandas as pd

# Example endpoint; replace with an actual API endpoint if available
url = "https://api.scryfall.com/cards/search"
params = {"q": "lightning bolt"}
response = get(url, impersonate="chrome",params=params)

if response.status_code == 200:
    data = response.json()
    print(data)
else:
    print(f'Error: {response.status_code}')
