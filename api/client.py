import time
import requests

BASE_URL = "https://api-web.nhle.com/v1"

def get(endpoint, retries=3, delay=0.5):
    url = f"{BASE_URL}/{endpoint}"

    for attempt in range(retries):
        response = requests.get(url, timeout=10)

        if response.status_code == 429:
            if attempt < retries - 1:
                time.sleep(2)
                continue
            response.raise_for_status()

        response.raise_for_status()
        time.sleep(delay)
        return response.json()
