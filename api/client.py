import requests

BASE_URL = "https://api-web.nhle.com/v1"

def get(endpoint):
    url = f"{BASE_URL}/{endpoint}"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()