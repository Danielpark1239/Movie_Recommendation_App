import os
import requests
import random

# Returns a valid proxy
def get_proxy():
    PROXIES_URL = os.environ['PROXIES_URL']
    proxiesResponse = requests.get(url=PROXIES_URL).text
    proxiesResponseList = proxiesResponse.splitlines()
    
    # Choose a random proxy
    proxy = random.choice(proxiesResponseList)
    print(f'Selected proxy: {proxy}')

    return {
        'http': 'http://' + proxy
    }

get_proxy()