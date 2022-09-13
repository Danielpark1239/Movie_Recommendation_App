import os
import requests
import random

# Returns a valid proxy from proxy.webshare.io
def get_proxy():
    PROXIES_URL = os.environ['PROXIES_URL']
    proxiesResponse = requests.get(url=PROXIES_URL).text
    proxiesResponseList = proxiesResponse.split()
    
    # Choose a random proxy
    proxy = random.choice(proxiesResponseList)
    print(f'Selected proxy: {proxy}')

    return {
        'http': proxy,
        'https': proxy
    }