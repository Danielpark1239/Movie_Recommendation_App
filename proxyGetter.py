import os
from dotenv import load_dotenv
import requests
import random

# Returns a valid proxy from proxy.webshare.io
def get_proxy():
    load_dotenv()
    PROXIES_URL = os.getenv('PROXIES_URL')
    proxiesResponse = requests.get(PROXIES_URL).text
    proxiesResponseList = proxiesResponse.split()
    
    # Choose a random proxy
    proxy = random.choice(proxiesResponseList)
    print(f'Selected proxy: {proxy}')

    return {
        'http': proxy,
        'https': proxy
    }