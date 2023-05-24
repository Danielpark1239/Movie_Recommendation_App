# RT Recommendations
Website that generates movie/TV show recommendations by scraping Rotten Tomatoes based on user filters
Built using Flask, Bulma, Celery, and BeautifulSoup

Hosted at [rt-recommendations.us-east-1.elasticbeanstalk.com/](https://rt-recommendations.us-east-1.elasticbeanstalk.com/)
- Deployed using AWS Elastic Beanstalk and Redis
- Note: This app may fail to generate recommendations if the Rotten Tomatoes website has changed. While I do try to maintain the website regularly, it won't be working all the time.

# Initial setup
### Install dependencies
Note: You could also use a conda env or any venv of your choice
```
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Prepare .env
To stop Rotten Tomatoes from blocking my requests, I use proxies. You could use any proxies of your choice; I'll be going over a free provider that I use:
1. Go to https://www.webshare.io/
2. Sign up/log in
3. In the left sidebar, click on "Proxy", then "List" in the drop-down. The default settings should be fine.
4. Click on "download", then copy the provided URL
5. In .env.template, replace "URL goes here" with the copied URL.
6. Rename .env.template to .env

It may be helpful to have US-based proxies, as the app was built to accomodate streaming platforms available in the US.

### Run local Redis
1. Install Redis for your OS here: https://redis.io/docs/getting-started/
2. Run `redis-server` in a separate window and verify that the displayed port is 6739

### Run Celery worker
1. Run `celery -A app.celery_app worker --loglevel=INFO -E` in a separate window

### Run Flask server
1. Run `flask run`

### Testing
1. Optional: Run `pytest tests.py` for some basic tests! (should take ~90s to run)

# Screenshots
![rt_home_page](https://github.com/Danielpark1239/RT_Recommendations/assets/90424009/d7ba1ab3-13cc-4703-93ad-208e768d4994)
![rt_movies](https://github.com/Danielpark1239/RT_Recommendations/assets/90424009/e95e5cc1-f59a-4061-aca6-de7d79fc7f3a)
![rt_movie_recs](https://github.com/Danielpark1239/RT_Recommendations/assets/90424009/ead41ca6-2ae7-458b-9c8b-35b4b50ade8d)

# Schema (Click to see arrows)
![RT-Recs-schema](https://github.com/Danielpark1239/RT_Recommendations/assets/90424009/c6b46c1c-fdfd-4bc8-af90-7921e081a2ac)

