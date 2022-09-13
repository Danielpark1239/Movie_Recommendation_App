import os
import requests
import random

# Returns a valid proxy from proxy.webshare.io
def get_proxy():
    PROXIES_URL = "https://proxy.webshare.io/api/v2/proxy/list/download/mtsihsevmmkmkcfraatxiiqwgazdbodfodlbdsgg/-/any/username/direct/-/" or os.environ['PROXIES_URL']
    proxiesResponse = requests.get(url=PROXIES_URL).text
    proxiesResponseList = proxiesResponse.splitlines()

    print(proxiesResponseList)
    
    # Choose a random proxy
    proxy = random.choice(proxiesResponseList)
    print(f'Selected proxy: {proxy}')

    return {
        'http': 'http://' + proxy
    }

get_proxy()