import time
import requests
from requests.exceptions import SSLError, ConnectionError, Timeout

BASE_URL = "https://api-web.nhle.com/v1"

def get(endpoint, retries=3, delay=0.5):
    url = f"{BASE_URL}/{endpoint}"
    backoff = delay

    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=10)
        except (SSLError, ConnectionError, Timeout) as e:
            if attempt < retries - 1:
                time.sleep(backoff)
                backoff *= 2
                continue
            raise

        # handle rate limiting from server
        if response.status_code == 429:
            if attempt < retries - 1:
                time.sleep(backoff)
                backoff *= 2
                continue
            response.raise_for_status()

        response.raise_for_status()
        time.sleep(delay)
        return response.json()
