import random
import time
import requests
from .exceptions import NetworkError

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36'
]

def get_random_user_agent():
    return random.choice(USER_AGENTS)

def add_delay():
    delay = random.uniform(1, 3)
    time.sleep(delay)

def make_request(url, max_retries=3):
    headers = {'User-Agent': get_random_user_agent()}
    for attempt in range(max_retries):
        try:
            add_delay()
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            print(f"Intento {attempt + 1} fallido. Error: {str(e)}")
            if attempt == max_retries - 1:
                raise NetworkError(f"Error al acceder a {url} después de {max_retries} intentos: {str(e)}")
    return None