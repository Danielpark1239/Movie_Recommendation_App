import os
import requests
import random
import user_agent

# Returns a valid proxy
def get_proxy():
    PROXIES_URL = os.environ['PROXIES_URL']
    proxiesResponse = requests.get(url=PROXIES_URL).text
    proxiesResponseList = proxiesResponse.split()
    
    # Choose a random proxy
    proxy = random.choice(proxiesResponseList)
    print(f'Selected proxy: {proxy}')

    return {
        'http': proxy
    }

# Should rename this module
def get_user_agent():
    agent = user_agent.generate_user_agent()
    return {'User-Agent': agent}