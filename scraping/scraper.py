import requests
import itertools
from bs4 import BeautifulSoup
import random
import re
from constants import *
import scraping.movieScraper as movieScraper
import scraping.showScraper as showScraper
from collections import deque
import time
import scraping.proxyGetter as proxyGetter
from app import celery_app
from celery.utils.log import get_task_logger
logger = get_task_logger(__name__)

# Generate movie URLs for scraping based on the filters
def generateMovieURLs(
    genres, ratings, platforms, tomatometerScore, audienceScore, limit, popular
):  
    try:
        start = time.time()
        URLs = []
        theatersURL = BASE_MOVIE_THEATERS_URL
        homeURL = BASE_MOVIE_HOME_URL
        
        # Set URL search queries
        audienceStrings = ["audience:upright~"]
        if audienceScore < FRESH_THRESHOLD:   
            audienceStrings.append("audience:spilled~")
        tomatometerStrings = ["critics:fresh~"]
        if tomatometerScore < FRESH_THRESHOLD:
            tomatometerStrings.append("critics:rotten~")
        if "all" in genres or len(genres) == 0:
            genreString = ""
        else:
            genreString = "genres:" + ",".join(genres) + "~"       
        if "all" in ratings or len(ratings) == 0:
            ratingString = ""
        else:
            ratingString = "ratings:" + ",".join(ratings) + "~"
        if len(platforms) == 0:
            platforms.append("all")
        # Determine the number of pages we need
        pageString = "sort:popular?page=5" # 5 is the new max?

        # Generate from theatersURL
        if "all" in platforms or "showtimes" in platforms:
            if "showtimes" in platforms:
                platforms.remove("showtimes")
            for audienceString in audienceStrings:
                for tomatometerString in tomatometerStrings:
                    URLs.append(
                        theatersURL + audienceString + tomatometerString \
                        + genreString + ratingString + pageString
                    )
        # Generate from homeURL
        if "all" in platforms or len(platforms) > 0:
            if "all" in platforms:
                platformString = ""
            else:
                platforms = [URL_PLATFORM_DICT[platform] for platform in platforms]
                platformString = "affiliates:" + ",".join(platforms) + "~"
            for audienceString in audienceStrings:
                for tomatometerString in tomatometerStrings:
                    URLs.append(
                        homeURL + audienceString + tomatometerString + platformString\
                        + genreString + ratingString + pageString
                    )
        if not popular:
            # To have a better chance of showing movies from other URLs
            random.shuffle(URLs)
        end = time.time()
        print(f'Time to generate movie URLs: {end - start}')
        print(f'Movie URLs: {URLs}')
        return URLs
    except:
        print("Error generating movie URLS")
        raise

# Generate TV show URLs to scrape based on the filters
def generateTVshowURLs(
    genres, ratings, platforms, tomatometerScore, audienceScore, limit, popular
):  
    try:
        start = time.time()
        URLs = []

        # Set URL search queries
        audienceStrings = ["audience:upright~"]
        if audienceScore < FRESH_THRESHOLD:   
            audienceStrings.append("audience:spilled~")
        tomatometerStrings = ["critics:fresh~"]
        if tomatometerScore < FRESH_THRESHOLD:
            tomatometerStrings.append("critics:rotten~")
        if "all" in genres or len(genres) == 0:
            genreString = ""
        else:
            genreString = "genres:" + ",".join(genres) + "~"
        if "all" in ratings or len(ratings) == 0:
            ratingString = ""
        else:
            ratingString = "ratings:" + ",".join(ratings) + "~"
        if len(platforms) == 0:
            platforms.append("all")
        if "all" in platforms:
            platformString = ""
        else:
            platforms = [URL_PLATFORM_DICT[platform] for platform in platforms]
            platformString = "affiliates:" + ",".join(platforms) + "~"
        pageString = "sort:popular?page=5"

        for audienceString in audienceStrings:
            for tomatometerString in tomatometerStrings:
                URLs.append(
                    BASE_TV_URL + audienceString + tomatometerString\
                    + platformString + genreString + ratingString + pageString
                )
        # To get a better chance of showing less popular shows
        if not popular:
            random.shuffle(URLs)
        end = time.time()
        print(f'Time to generate TV Show URLs: {end - start}')
        print(f'TV show URLs: {URLs}')
        return URLs

    except:
        print("Error generating TV show URLs")
        raise

# return a dictionary of movie recommendations based on the URLs and filters,
# setting the job meta result; if key is passed, use background job
@celery_app.task(bind=True, track_started=True, ignore_result=False, name="scraping/scraper/scrapeMovies")
def scrapeMovies(self, URLs, tomatometerScore, audienceScore, limit, year=None,
                 skipURL=None, key=None, similarProgress=None, similarTask=None):
    try:
        start = time.time()
        if key and similarProgress is None:
            self.update_state(
                state="STARTED",
                meta={'progress': 0}
            )

        # array of row arrays; each row array contains up to 4 dictionaries/movies
        movieInfo = [[]]
        movieCount = 0
        movieDict = {} # Keys contain movie names; used to avoid duplicates
        useRandom = True if tomatometerScore <= RANDOM_THRESHOLD and \
        audienceScore <= RANDOM_THRESHOLD else False
        desiredInfoCategories = [
            "Rating:", "Genre:", "Original Language:", "Release Date (Theaters):",
            "Release Date (Streaming):", "Runtime:", "Director:", "Producer:", "Writer:"
        ]
        proxies = proxyGetter.get_proxy()
        headers = proxyGetter.get_user_agent()
        print(URLs)
        for url in URLs:
            if movieCount == limit:
                break
            
            html_text = requests.get(
                url=url,
                headers=headers,
                proxies=proxies
            ).text
            # check if the request is getting blocked
            print(f"HTML_TEXT OUTPUT: {html_text[:150]}")

            # Scrape movies page
            moviePageSoup = BeautifulSoup(html_text, "lxml")
            oldMovies = moviePageSoup.find_all(
                "a", 
                attrs={
                    "href": re.compile("/m/"),
                    "data-qa": "discovery-media-list-item"
                }
            )
            movies = moviePageSoup.find_all(
                "a", 
                attrs={
                    "href": re.compile("/m/"),
                    "data-qa": "discovery-media-list-item-caption"
                }
            )
            for movie in itertools.chain(oldMovies or [], movies or []):
                if movieCount == limit:
                    break
                currTime = time.time()
                if currTime - start > TIMEOUT:
                    break
                
                # 80% chance of movie being added to recommendations
                # if scores are below 80
                # --> Users get different movies each time for the same inputs
                if useRandom and random.randint(0,4) == 0:
                    continue
                url = BASE_URL + movie["href"]
                if skipURL and skipURL == url:
                    continue
                
                # Filter based on scores
                scoreData = movie.find("score-pairs")
                if scoreData["audiencescore"] == "" or int(scoreData["audiencescore"]) < audienceScore:
                    continue
                if scoreData["criticsscore"] == "" or int(scoreData["criticsscore"]) < tomatometerScore:
                    continue
                
                movieInfoDict = {
                    "audienceScore": scoreData["audiencescore"],
                    "criticsScore": scoreData["criticsscore"],
                    "url": url
                }
                if year:
                    movieInfoDict["similar"] = "movie"

                # Get additional data about the movie by looking at its page
                movie_html_text = requests.get(
                    url=url,
                    headers=headers,
                    proxies=proxies
                ).text
                movieSoup = BeautifulSoup(movie_html_text, "lxml")

                name = movieScraper.getName(movieSoup)
                if name is None or name in movieDict: # Avoid dups
                    continue
                movieDict[name] = True
                movieInfoDict["name"] = name
                movieScraper.setPosterImage(movieSoup, movieInfoDict)
                movieScraper.setPlatforms(movieSoup, movieInfoDict)
                movieScraper.setCast(movieSoup, movieInfoDict)

                # Additional information (rating, genre, etc.)
                additionalInfo = movieSoup.find_all(
                    "b", 
                    attrs={"data-qa": "movie-info-item-label"}
                )
                # If true, year filter failed; break
                yearFlag = False
                for info in additionalInfo:
                    # Set info depending on category
                    if info.text == desiredInfoCategories[0]:
                        movieScraper.setRating(info, movieInfoDict)
                    elif info.text == desiredInfoCategories[1]:
                        movieScraper.setGenres(info, movieInfoDict)
                    elif info.text == desiredInfoCategories[2]:
                        movieScraper.setLanguage(info, movieInfoDict)
                    elif info.text == desiredInfoCategories[3]:
                        if year:
                            yearFilter = movieScraper.setDateWithFilter(
                                info, movieInfoDict, year
                            )
                            if not yearFilter:
                                yearFlag = True
                                break
                        else:
                            movieScraper.setDate(info, movieInfoDict, "theaters")
                    elif info.text == desiredInfoCategories[4]:
                        movieScraper.setDate(info, movieInfoDict, "streaming")
                    elif info.text == desiredInfoCategories[5]:
                        movieScraper.setRuntime(info, movieInfoDict)
                    elif info.text == desiredInfoCategories[6]:
                        movieScraper.setDirectors(info, movieInfoDict)
                    elif info.text == desiredInfoCategories[7]:
                        movieScraper.setProducers(info, movieInfoDict)
                    elif info.text == desiredInfoCategories[8]:
                        movieScraper.setWriters(info, movieInfoDict)
                    else:
                        continue   
                if yearFlag:
                    continue
                if similarProgress is not None:
                    movieInfoDict['type'] = 'movie'

                print(name)
                # if the last row is full, create a new row
                if len(movieInfo[-1]) == 4:
                    movieInfo.append([movieInfoDict])
                else:
                    movieInfo[-1].append(movieInfoDict)

                movieCount += 1
                if key:
                    if similarProgress is None:
                        self.update_state(
                            state="STARTED",
                            meta={'progress': int((movieCount / limit) * 100)}
                        )
                    else:
                        similarTask.update_state(
                            state="STARTED",
                            meta={'progress': int((movieCount + similarProgress) / (limit + similarProgress) * 100)}
                        )
        end = time.time()
        print(f'Time to generate movie recs: {end - start}')
        if key and similarProgress is None:
            self.update_state(
                state="SUCCESS",
                meta={
                    'result': "recommendations/" + self.request.id,
                    'key': key,
                    'movieInfo': movieInfo
                }
            )
        return movieInfo
    except:
        print("Error scraping movies")
        raise

# return a dictionary of TV show recommendations based on the URLs and filters,
# setting the job meta result; if key is passed, use background job
@celery_app.task(bind=True, track_started=True, ignore_result=False, name="scraping/scraper/scrapeTVshows")
def scrapeTVshows(self, URLs, tomatometerScore, audienceScore, limit, year=None, 
                  skipURL=None, key=None, similarProgress=None, similarTask=None):
    try:
        start = time.time()
        if key and similarProgress is None:
            self.update_state(
                state="STARTED",
                meta={'progress': 0}
            )

        # array of row arrays; each row array contains up to 4 dictionaries/shows
        tvShowInfo = [[]]
        tvShowCount = 0
        tvShowDict = {} # Keys contain tv show names; used to avoid duplicates
        useRandom = True if tomatometerScore <= RANDOM_THRESHOLD and \
        audienceScore <= RANDOM_THRESHOLD else False
        proxies = proxyGetter.get_proxy()
        headers = proxyGetter.get_user_agent()
        print(URLs)

        for url in URLs:
            if tvShowCount == limit:
                break

            html_text = requests.get(
                url=url,
                headers=headers,
                proxies=proxies
            ).text
            # Debugging: check if the request is getting blocked
            print(f"HTML_TEXT OUTPUT: {html_text[:150]}")

            # Scrape tv shows page
            tvShowPageSoup = BeautifulSoup(html_text, "lxml")
            tvShows = tvShowPageSoup.find_all(
                "a", 
                attrs={
                    "href": re.compile("/tv/"),
                    "data-qa": "discovery-media-list-item"
                }
            )
            for tvShow in tvShows:
                if tvShowCount == limit:
                    break
                currTime = time.time()
                if currTime - start > TIMEOUT:
                    break
                if useRandom and random.randint(0,4) == 0:
                    continue
                url = BASE_URL + tvShow["href"]
                if skipURL and skipURL == url:
                    continue
                
                # Filter based on scores
                data = tvShow.find("div", slot="caption")
                scores = data.contents[1]
                if scores["audiencescore"] == "" or int(scores["audiencescore"]) < audienceScore:
                    continue
                if scores["criticsscore"] == "" or int(scores["criticsscore"]) < tomatometerScore:
                    continue

                tvShowInfoDict = {
                    "audienceScore": scores["audiencescore"],
                    "criticsScore": scores["criticsscore"],
                    "url": url
                }
                if year:
                    tvShowInfoDict["similar"] = "tv"

                # Get additional data about the show by looking at its page
                tvshow_html_text = requests.get(
                    url=url,
                    headers=headers,
                    proxies=proxies
                ).text
                tvShowSoup = BeautifulSoup(tvshow_html_text, "lxml")

                name = showScraper.getName(tvShowSoup)
                if name is None or name in tvShowDict: # Avoid dups
                    continue
                tvShowDict[name] = True
                tvShowInfoDict["name"] = name
                if year:
                    yearFilter = showScraper.setPremiereDateWithFilter(
                        tvShowSoup, tvShowInfoDict, year
                    )
                    if not yearFilter:
                        continue
                else:
                    showScraper.setPremiereDate(tvShowSoup, tvShowInfoDict)
                showScraper.setPosterImage(tvShowSoup, tvShowInfoDict)
                showScraper.setPlatforms(tvShowSoup, tvShowInfoDict)
                showScraper.setNetwork(tvShowSoup, tvShowInfoDict)
                showScraper.setGenre(tvShowSoup, tvShowInfoDict)
                showScraper.setCreators(tvShowSoup, tvShowInfoDict)
                showScraper.setProducers(tvShowSoup, tvShowInfoDict)
                showScraper.setCast(tvShowSoup, tvShowInfoDict)
                if similarProgress is not None:
                    tvShowInfoDict['type'] = 'tv'

                print(name)
                # if the last row is full, create a new row
                if len(tvShowInfo[-1]) == 4:
                    tvShowInfo.append([tvShowInfoDict])
                else:
                    tvShowInfo[-1].append(tvShowInfoDict)

                tvShowCount += 1
                if key:
                    if similarProgress is None:
                        self.update_state(
                            state="STARTED",
                            meta={'progress': int((tvShowCount / limit) * 100)}  
                        )
                    else:
                        similarTask.update_state(
                            state="STARTED",
                            meta={'progress': int(((tvShowCount + similarProgress) / (limit + similarProgress)) * 100)}
                        )
        end = time.time()
        print(f'Time it takes to generate tv show recs: {end - start}')
        if key and similarProgress is None:
            self.update_state(
                state="SUCCESS",
                meta={
                    'result': 'recommendations/' + self.request.id,
                    'key': key,
                    'tvShowInfo': tvShowInfo 
                }
            )
        return tvShowInfo
    except:
        print("Error scraping TV shows")
        raise

# return a dictionary of actor movie/show recommendations based on the 
# URLs and filters, setting the job meta result; if key is passed, use background job
@celery_app.task(bind=True, track_started=True, ignore_result=False, name="scraping/scraper/scrapeActor")
def scrapeActor(self, filterData, key=None):
    try:
        start = time.time()
        if key:
            self.update_state(
                state="STARTED",
                meta={'progress': 0}
            )
        count = 0
        filmographyInfo = [[]]
        proxies = proxyGetter.get_proxy()
        headers = proxyGetter.get_user_agent()
        html_text = requests.get(
            url=filterData["actorURL"],
            headers=headers,
            proxies=proxies
        ).text
        # check if the request is getting blocked
        print(f"HTML_TEXT OUTPUT: {html_text[:150]}")
        soup = BeautifulSoup(html_text, "lxml")

        # If URL is invalid, return None
        main_page_content = soup.find("div", attrs={"id": "main-page-content"})
        if main_page_content is not None:
            h1 = main_page_content.find("h1")
            if h1.text.strip() == "404 - Not Found":
                if key:
                    self.update_state(
                        state="SUCCESS",
                        meta={
                            'result': "recommendations/" + self.request.id,
                            'key': key,
                            'actorInfo': None
                        }
                    )
                    return
                else:
                    return None

        # Scrape movies
        if filterData["category"] == "movie":
            movies = soup.find_all("tr", attrs={
                "data-qa": "celebrity-filmography-movies-trow"
            })
            for movie in movies:
                if count == filterData["limit"]:
                    break
                currTime = time.time()
                if currTime - start > TIMEOUT:
                    break
                name = movie["data-title"]
                boxOffice = int(movie["data-boxoffice"]) if movie["data-boxoffice"] else 0
                year = int(movie["data-year"])
                tomatometerScore = int(movie["data-tomatometer"])
                audienceScore = int(movie["data-audiencescore"])
                role = movie.find("td", attrs={"class": "celebrity-filmography__credits"})
                if role:
                    role = role.text.strip()

                # Filter by scores
                if tomatometerScore < filterData["tomatometerScore"]:
                    continue
                if audienceScore < filterData["audienceScore"]:
                    continue

                # Filter by role if specified
                roles = filterData["roles"]
                if role and "all" not in roles:
                    if ("(Character)" in role or "Self" in role) and "character" not in roles:
                        continue
                    elif "(Voice)" in role and "voice" not in roles:
                        continue
                    elif "(Character)" not in role and "Self" not in role and \
                    "(Voice)" not in role and "other" not in roles:
                        continue
                # Filter by box office
                if boxOffice // 1000000 < filterData["boxOffice"]:
                    continue
                # Filter by year
                if year < filterData["oldestYear"]:
                    continue

                # Search movie page
                href = movie.find("a")['href']
                moviePageURL = BASE_URL + href
                movie_html_text = requests.get(
                    url=moviePageURL,
                    headers=headers,
                    proxies=proxies
                ).text
                movieSoup = BeautifulSoup(movie_html_text, "lxml")
                movieInfoDict = {
                    "type": "movie",
                    "name": name,
                    "audienceScore": audienceScore,
                    "criticsScore": tomatometerScore,
                    "url": moviePageURL,
                    "role": role.replace(",", ", "),
                    "boxOffice": "$" + str(boxOffice // 1000000) + "M",
                    "year": year
                }
                # Available streaming platforms
                # If none of the movie's platforms match the filter, skip
                platformFlag = movieScraper.setPlatformsWithFilter(
                    movieSoup, movieInfoDict, filterData["platforms"]
                )
                if not platformFlag:
                    continue
                # Additional information (rating, genre, original language, runtime)
                additionalInfo = movieSoup.find_all(
                    "b", 
                    attrs={"data-qa": "movie-info-item-label"}
                )
                # If a movie doesn't pass the rating filter, skip it
                ratingFlag = False
                # If a movie doesn't pass the genre filter, skip it
                genreFlag = False

                # Filter and format data depending on category
                for info in additionalInfo:
                    if info.text == "Rating:":
                        ratingFlag = movieScraper.setRatingWithFilter(
                            info, movieInfoDict, filterData["ratings"]
                        )
                        if not ratingFlag:
                            break
                    elif info.text == "Genre:":
                        genreFlag = movieScraper.setGenresWithFilter(
                            info, movieInfoDict, filterData["genres"]
                        )
                        if not genreFlag:
                            break
                    elif info.text == "Original Language:":
                        movieScraper.setLanguage(info, movieInfoDict)
                    elif info.text == "Runtime:":
                        movieScraper.setRuntime(info, movieInfoDict)
                    else:
                        continue
                if not ratingFlag or not genreFlag:
                    continue
                movieScraper.setPosterImage(movieSoup, movieInfoDict)
                print(name)
                # if the last row is full, create a new row
                if len(filmographyInfo[-1]) == 4:
                    filmographyInfo.append([movieInfoDict])
                else:
                    filmographyInfo[-1].append(movieInfoDict)

                count += 1
                if key:
                    self.update_state(
                        state="STARTED",
                        meta={'progress': int((count / filterData['limit']) * 100)}
                    )

        # Scrape TV shows
        elif filterData["category"] == "tv":
            tvShows = soup.find_all("tr", attrs={
                "data-qa": "celebrity-filmography-tv-trow"
            })
            for tvShow in tvShows:
                if count == filterData["limit"]:
                    break
                currTime = time.time()
                if currTime - start > TIMEOUT:
                    break
                name = tvShow["data-title"]
                year = int(tvShow["data-appearance-year"][1:5])
                yearString = tvShow["data-appearance-year"][1:-1].replace(",", ", ")
                tomatometerScore = int(tvShow["data-tomatometer"])
                audienceScore = int(tvShow["data-audiencescore"])
                role = tvShow.contents[7].text.strip()

                # Filter by scores
                if tomatometerScore < filterData["tomatometerScore"]:
                    continue
                if audienceScore < filterData["audienceScore"]:
                    continue

                # Filter by role if specified
                roles = filterData["roles"]
                if "all" not in roles:
                    if ("(Character)" in role or "Self" in role) and "character" not in roles:
                        continue
                    elif "(Voice)" in role and "voice" not in roles:
                        continue
                    elif "(Character)" not in role and "Self" not in role and \
                    "(Voice)" not in role and "other" not in roles:
                        continue
                    
                # Filter by year
                if year < filterData["oldestYear"]:
                    continue

                # Search tv show page
                showPageURL = BASE_URL + tvShow.contents[5].contents[1]["href"]
                show_html_text = requests.get(
                    url=showPageURL,
                    headers=headers,
                    proxies=proxies
                ).text
                showSoup = BeautifulSoup(show_html_text, "lxml")

                showInfoDict = {
                    "type": "tv",
                    "name": name,
                    "audienceScore": audienceScore,
                    "criticsScore": tomatometerScore,
                    "url": showPageURL,
                    "role": role.replace(",", ", "),
                    "years": yearString
                }
                
                # Genre
                genreFlag = showScraper.setGenreWithFilter(
                    showSoup, showInfoDict, filterData["genres"]
                )
                if not genreFlag:
                    continue

                # Available streaming platforms
                # If none of the show's platforms match the filter, skip
                platformFlag = showScraper.setPlatformsWithFilter(
                    showSoup, showInfoDict, filterData["platforms"]
                )
                if not platformFlag:
                    continue
                showScraper.setNetwork(showSoup, showInfoDict)
                showScraper.setPosterImage(showSoup, showInfoDict)

                print(name)
                # if the last row is full, create a new row
                if len(filmographyInfo[-1]) == 4:
                    filmographyInfo.append([showInfoDict])
                else:
                    filmographyInfo[-1].append(showInfoDict)

                count += 1
                if key:
                    self.update_state(
                        state="STARTED",
                        meta={'progress': int((count / filterData['limit']) * 100)}
                    )

        end = time.time()
        print(f'Time to generate actor recs: {end - start}')
        if key:
            self.update_state(
                state="SUCCESS",
                meta={
                    'result': "recommendations/" + self.request.id,
                    'key': key,
                    'actorInfo': filmographyInfo
                }
            )
        return filmographyInfo
    
    except:
        print("Error scraping actor")
        raise

# return a dictionary of director or producer movie/show recommendations
# based on the URLs and filters, setting the job meta result
# if key is passed, use background job
@celery_app.task(bind=True, track_started=True, ignore_result=False, name="scraping/scraper/scrapeDirectorProducer")
def scrapeDirectorProducer(self, filterData, type, key=None):
    try:
        start = time.time()
        if key:
            self.update_state(
                state="STARTED",
                meta={'progress': 0}
            )
        count = 0
        filmographyInfo = [[]]
        proxies = proxyGetter.get_proxy()
        headers = proxyGetter.get_user_agent()

        html_text = requests.get(
            url=filterData["url"],
            headers=headers,
            proxies=proxies
        ).text
        # check if the request is getting blocked
        print(f"HTML_TEXT OUTPUT: {html_text[:150]}")
        soup = BeautifulSoup(html_text, "lxml")

        # If URL is invalid, return None
        main_page_content = soup.find("div", attrs={"id": "main-page-content"})
        if main_page_content is not None:
            h1 = main_page_content.find("h1")
            if h1.text.strip() == "404 - Not Found":
                if key:
                    self.update_state(
                        state="SUCCESS",
                        meta={
                            'result': "recommendations/" + self.request.id,
                            'key': key,
                            'filmographyInfo': None
                        }
                    )
                    return
                else:
                    return None

        # Scrape movies
        if filterData["category"] == "movie":
            movies = soup.find_all("tr", attrs={
                "data-qa": "celebrity-filmography-movies-trow"
            })
            for movie in movies:
                if count == filterData["limit"]:
                    break
                currTime = time.time()
                if currTime - start > TIMEOUT:
                    break
                name = movie["data-title"]
                boxOffice = int(movie["data-boxoffice"]) if movie["data-boxoffice"] else 0
                year = int(movie["data-year"])
                tomatometerScore = int(movie["data-tomatometer"])
                audienceScore = int(movie["data-audiencescore"])
                role = movie.contents[7].text.strip()

                # Filter by scores
                if tomatometerScore < filterData["tomatometerScore"]:
                    continue
                if audienceScore < filterData["audienceScore"]:
                    continue
                # Filter by role
                if type == "director":
                    desiredRole = "Director"
                elif type == "producer":
                    desiredRole = "Producer"
                
                if desiredRole not in role:
                    continue
                # Filter by box office
                if boxOffice // 1000000 < filterData["boxOffice"]:
                    continue
                # Filter by year
                if year < filterData["oldestYear"]:
                    continue
                # Search movie page
                moviePageURL = BASE_URL + movie.contents[5].contents[1]["href"]
                movie_html_text = requests.get(
                    url=moviePageURL,
                    headers=headers,
                    proxies=proxies
                ).text
                movieSoup = BeautifulSoup(movie_html_text, "lxml")

                movieInfoDict = {
                    "type": "movie",
                    "name": name,
                    "audienceScore": audienceScore,
                    "criticsScore": tomatometerScore,
                    "url": moviePageURL,
                    "boxOffice": "$" + str(boxOffice // 1000000) + "M",
                }

                # Available streaming platforms
                # If none of the movie's platforms match the filter, skip
                platformFlag = movieScraper.setPlatformsWithFilter(
                    movieSoup, movieInfoDict, filterData["platforms"]
                )
                if not platformFlag:
                    continue

                # Additional information
                additionalInfo = movieSoup.find_all(
                    "b", 
                    attrs={"data-qa": "movie-info-item-label"}
                )
                # If a movie doesn't pass the rating filter, skip it
                ratingFlag = False
                # If a movie doesn't pass the genre filter, skip it
                genreFlag = False

                for info in additionalInfo:
                    # Filter and format data depending on category
                    if info.text == "Rating:":
                        ratingFlag = movieScraper.setRatingWithFilter(
                            info, movieInfoDict, filterData["ratings"]
                        )
                        if not ratingFlag:
                            break
                    elif info.text == "Genre:":
                        genreFlag = movieScraper.setGenresWithFilter(
                            info, movieInfoDict, filterData["genres"]
                        )
                        if not genreFlag:
                            break
                    elif info.text == "Original Language:":
                        movieScraper.setLanguage(info, movieInfoDict)
                    elif info.text == "Runtime:":
                        movieScraper.setRuntime(info, movieInfoDict)
                    elif info.text == "Release Date (Theaters):":
                        movieScraper.setDate(info, movieInfoDict, "theaters")
                    elif info.text == "Release Date (Streaming):":  
                        movieScraper.setDate(info, movieInfoDict, "streaming")
                    elif info.text == "Director:":
                        movieScraper.setDirectors(info, movieInfoDict)
                    elif info.text == "Producer:":
                        movieScraper.setProducers(info, movieInfoDict)
                    elif info.text == "Writer:":
                        movieScraper.setWriters(info, movieInfoDict)
                    else:
                        continue
                if not ratingFlag or not genreFlag:
                    continue
                movieScraper.setCast(movieSoup, movieInfoDict)
                movieScraper.setPosterImage(movieSoup, movieInfoDict)

                print(name)
                # if the last row is full, create a new row
                if len(filmographyInfo[-1]) == 4:
                    filmographyInfo.append([movieInfoDict])
                else:
                    filmographyInfo[-1].append(movieInfoDict)

                count += 1
                if key:
                    self.update_state(
                        state="STARTED",
                        meta={'progress': int((count / filterData['limit']) * 100)}  
                    )

        # Scrape TV shows
        elif filterData["category"] == "tv":
            tvShows = soup.find_all("tr", attrs={
                "data-qa": "celebrity-filmography-tv-trow"
            })
            for tvShow in tvShows:
                if count == filterData["limit"]:
                    break
                currTime = time.time()
                if currTime - start > TIMEOUT:
                    break
                name = tvShow["data-title"]
                year = int(tvShow["data-appearance-year"][1:5])
                yearString = tvShow["data-appearance-year"][1:-1].replace(",", ", ")
                tomatometerScore = int(tvShow["data-tomatometer"])
                audienceScore = int(tvShow["data-audiencescore"])
                role = tvShow.contents[7].text.strip()

                # Filter by scores
                if tomatometerScore < filterData["tomatometerScore"]:
                    continue
                if audienceScore < filterData["audienceScore"]:
                    continue
                # Filter by role
                if type == "director":
                    desiredRole = "Director"
                elif type == "producer":
                    desiredRole = "Producer"
                if desiredRole not in role:
                    continue
                # Filter by year
                if year < filterData["oldestYear"]:
                    continue
                # Search tv show page
                showPageURL = BASE_URL + tvShow.contents[5].contents[1]["href"]
                show_html_text = requests.get(
                    url=showPageURL,
                    headers=headers,
                    proxies=proxies
                ).text
                showSoup = BeautifulSoup(show_html_text, "lxml")

                showInfoDict = {
                    "type": "tv",
                    "name": name,
                    "audienceScore": audienceScore,
                    "criticsScore": tomatometerScore,
                    "url": showPageURL,
                    "years": yearString
                }
                
                # Genre
                genreFlag = showScraper.setGenreWithFilter(
                    showSoup, showInfoDict, filterData["genres"]
                )
                if not genreFlag:
                    continue
                # Available streaming platforms
                # If none of the show's platforms match the filter, skip
                platformFlag = showScraper.setPlatformsWithFilter(
                    showSoup, showInfoDict, filterData["platforms"]
                )
                if not platformFlag:
                    continue
                showScraper.setNetwork(showSoup, showInfoDict)
                showScraper.setPremiereDate(showSoup, showInfoDict)
                showScraper.setCreators(showSoup, showInfoDict)
                showScraper.setProducers(showSoup, showInfoDict)
                showScraper.setCast(showSoup, showInfoDict)
                showScraper.setPosterImage(showSoup, showInfoDict)

                print(name)
                # if the last row is full, create a new row
                if len(filmographyInfo[-1]) == 4:
                    filmographyInfo.append([showInfoDict])
                else:
                    filmographyInfo[-1].append(showInfoDict)
                
                count += 1
                if key:
                    self.update_state(
                        state="STARTED",
                        meta={'progress': int((count / filterData['limit']) * 100)}  
                    )
        end = time.time()
        print(f'Time to generate director/producer recs: {end - start}')
        if key:
            self.update_state(
                state="SUCCESS",
                meta={
                    'result': 'recommendations/' + self.request.id,
                    'key': key,
                    'filmographyInfo': filmographyInfo 
                }
            )
        return filmographyInfo
    except:
        print("Error scraping director/producer")
        raise

# return a dictionary of similar movie/show recommendations based on the 
# URLs and filters, setting the job meta result
# if key is passed, use background job
@celery_app.task(bind=True, track_started=True, ignore_result=False, name="scraping/scraper/scrapeSimilar")
def scrapeSimilar(self, filterData, key=None):
    try:
        start = time.time()
        addedCount = 0
        limit = filterData["limit"]
        tomatometerScore = filterData["tomatometerScore"]
        audienceScore = filterData["audienceScore"]
        if key:
            self.update_state(
                state="STARTED",
                meta={'progress': 0}
            )
        similarInfo = [[]]
        proxies = proxyGetter.get_proxy()
        headers = proxyGetter.get_user_agent()
        html_text = requests.get(
            url=filterData["url"],
            headers=headers,
            proxies=proxies
        ).text
        # check if the request is getting blocked
        print(f"HTML_TEXT OUTPUT: {html_text[:150]}")
        soup = BeautifulSoup(html_text, "lxml")

        # If URL is invalid, return None
        main_page_content = soup.find("div", attrs={"id": "main-page-content"})
        if main_page_content is not None:
            h1 = main_page_content.find("h1")
            if h1.text.strip() == "404 - Not Found":
                if key:
                    self.update_state(
                        state="SUCCESS",
                        meta={
                            'result': "recommendations/" + self.request.id,
                            'key': key,
                            'similarInfo': None
                        }
                    )
                    return
                else:
                    return None

        # Breadth-First-search; intuition is that media that
        # have fewer steps to each other are more closely related
        queue = deque()
        marked = {
            filterData["url"]: True
        }
        carouselItems = soup.find_all(
            "tiles-carousel-responsive-item", attrs={"slot": "tile"}
        )
        if carouselItems and len(carouselItems) > 0:
            for carouselItem in carouselItems:
                a = carouselItem.find("a")
                if not a:
                    continue
                href = a['href']
                # Ignore trailers and other links
                if href.count('/') > 2:
                    continue
                itemURL = BASE_URL + href
                marked[itemURL] = True
                queue.append(itemURL)
        # If no similar items, default to scrapeMovies and scrapeTvShows
        if len(queue) == 0:
            platforms = filterData["platforms"]
            oldestYear = filterData["oldestYear"]
            if "/m/" in filterData["url"]:
                genres = movieScraper.getGenreArray(soup)
                ratings = movieScraper.getRatingArray(soup)
                URLs = generateMovieURLs(
                    genres, ratings, platforms, tomatometerScore, audienceScore,
                    limit, True
                )
                if key:
                    res = scrapeMovies(
                        URLs, tomatometerScore, audienceScore, limit, 
                        year=oldestYear, skipURL=filterData["url"], key=key,
                        similarProgress=0, similarTask=self
                    )
                    self.update_state(
                        state="SUCCESS",
                        meta={
                            'result': 'recommendations/' + self.request.id,
                            'key': key,
                            'similarInfo': res 
                        }
                    )
                    return
                else:
                    return scrapeMovies(
                        URLs, tomatometerScore, audienceScore, limit, 
                        year=oldestYear, skipURL=filterData["url"]
                    )
            elif "/tv/" in filterData["url"]:
                genres = showScraper.getGenreArray(soup)
                ratings = ["all"]
                URLs = generateTVshowURLs(
                    genres, ratings, platforms, tomatometerScore, audienceScore,
                    limit, True
                )
                if key:
                    res = scrapeTVshows(
                        URLs, tomatometerScore, audienceScore, limit, 
                        year=oldestYear, skipURL=filterData["url"], key=key,
                        similarProgress=0, similarTask=self
                    )
                    self.update_state(
                        state="SUCCESS",
                        meta={
                            'result': 'recommendations/' + self.request.id,
                            'key': key,
                            'similarInfo': res 
                        }
                    )
                    return
                else:
                    return scrapeTVshows(
                        URLs, tomatometerScore, audienceScore, limit, 
                        year=oldestYear, skipURL=filterData["url"]
                    )
        while len(queue) > 0:
            if addedCount == limit:
                break
            currTime = time.time()
            if currTime - start > TIMEOUT:
                break
            url = queue.popleft()
            html_text = requests.get(
                url=url,
                headers=headers,
                proxies=proxies
            ).text
            itemSoup = BeautifulSoup(html_text, "lxml")

            # Add similar items to BFS queue
            carouselItems = soup.find_all(
                "tiles-carousel-responsive-item", attrs={"slot": "tile"}
            )
            if not carouselItems or len(carouselItems) == 0:
                continue
            for carouselItem in carouselItems:
                a = carouselItem.find("a")
                if not a:
                    continue
                href = a['href']
                # Ignore trailers and other links
                if href.count('/') > 2:
                    continue
                itemURL = BASE_URL + href
                # If we've already marked the item, skip over it
                if marked.get(itemURL, None) is not None:
                    continue
                marked[itemURL] = True
                queue.append(itemURL)

            if "/m/" in url:
                name = movieScraper.getName(itemSoup)
                if name is None:
                    continue
                # Filter based on scores
                criticsScoreLabel = itemSoup.find("score-icon-critic")
                audienceScoreLabel = itemSoup.find("score-icon-audience")
                if not audienceScoreLabel or int(audienceScoreLabel['percentage']) < audienceScore:
                    continue
                if not criticsScoreLabel or int(criticsScoreLabel['percentage']) < tomatometerScore:
                    continue

                similarInfoDict = {
                    "type": "movie",
                    "name": name,
                    "url": url,
                    "criticsScore": int(criticsScoreLabel['percentage']),
                    "audienceScore": int(audienceScoreLabel['percentage']),
                    "similar": "both"
                }

                platformFlag = movieScraper.setPlatformsWithFilter(
                    itemSoup, similarInfoDict, filterData["platforms"]
                )
                if not platformFlag:
                    continue
                # Additional information (rating, genre, etc.)
                additionalInfo = itemSoup.find_all(
                    "b", 
                    attrs={"data-qa": "movie-info-item-label"}
                )
                dateFlag = False
                for info in additionalInfo:
                    # Set info depending on category
                    if info.text == "Rating:":
                        movieScraper.setRating(info, similarInfoDict)
                    elif info.text == "Genre:":
                        movieScraper.setGenres(info, similarInfoDict)
                    elif info.text == "Original Language:":
                        movieScraper.setLanguage(info, similarInfoDict)
                    elif info.text == "Release Date (Theaters):":
                        dateFlag = movieScraper.setDateWithFilter(
                            info, similarInfoDict, filterData["oldestYear"]
                        )
                        if not dateFlag:
                            break
                    elif info.text == "Release Date (Streaming):":
                        movieScraper.setDate(info, similarInfoDict, "streaming")
                    elif info.text == "Runtime:":
                        movieScraper.setRuntime(info, similarInfoDict)
                    elif info.text == "Director:":
                        movieScraper.setDirectors(info, similarInfoDict)
                    elif info.text == "Producer:":
                        movieScraper.setProducers(info, similarInfoDict)
                    elif info.text == "Writer:":
                        movieScraper.setWriters(info, similarInfoDict)
                    else:
                        continue
                if not dateFlag:
                    continue
                movieScraper.setPosterImage(itemSoup, similarInfoDict)
                movieScraper.setCast(itemSoup, similarInfoDict)
                print(name)
            
            elif "/tv/" in url:         
                name = showScraper.getName(itemSoup)
                if name is None:
                    continue
                # Filter based on scores
                criticsScoreLabel = itemSoup.find("score-icon-critic")
                audienceScoreLabel = itemSoup.find("score-icon-audience")
                if not audienceScoreLabel or int(audienceScoreLabel['percentage']) < audienceScore:
                    continue
                if not criticsScoreLabel or int(criticsScoreLabel['percentage']) < tomatometerScore:
                    continue
                similarInfoDict = {
                    "type": "tv",
                    "name": name,
                    "audienceScore": int(audienceScoreLabel['percentage']),
                    "criticsScore": int(criticsScoreLabel['percentage']),
                    "url": url,
                    "similar": "both"
                }

                showScraper.setPosterImage(itemSoup, similarInfoDict)
                platformFlag = showScraper.setPlatformsWithFilter(
                    itemSoup, similarInfoDict, filterData["platforms"]
                )
                if not platformFlag:
                    continue
                showScraper.setNetwork(itemSoup, similarInfoDict)
                dateFlag = showScraper.setPremiereDateWithFilter(
                    itemSoup, similarInfoDict, filterData["oldestYear"]
                )
                if not dateFlag:
                    continue
                showScraper.setGenre(itemSoup, similarInfoDict)
                showScraper.setCreators(itemSoup, similarInfoDict)
                showScraper.setProducers(itemSoup, similarInfoDict)
                showScraper.setCast(itemSoup, similarInfoDict)
                print(name)
            
            # if the last row is full, create a new row
            if len(similarInfo[-1]) == 4:
                similarInfo.append([similarInfoDict])
            else:
                similarInfo[-1].append(similarInfoDict)
            addedCount += 1
            if key:
                self.update_state(
                    state="STARTED",
                    meta={'progress': int((addedCount / limit) * 100)}  
                )

        # If we need more items, use scrapeMovies and scrapeTVshows
        if addedCount < limit:
            platforms = filterData["platforms"]
            oldestYear = filterData["oldestYear"]
            if "/m/" in filterData["url"]:
                genres = movieScraper.getGenreArray(soup)
                ratings = movieScraper.getRatingArray(soup)
                URLs = generateMovieURLs(
                    genres, ratings, platforms, tomatometerScore, audienceScore,
                    limit - addedCount, True
                )
                res =  scrapeMovies(
                    URLs, tomatometerScore, audienceScore, limit - addedCount, 
                    year=oldestYear, skipURL=filterData["url"], key=key,
                    similarProgress=addedCount, similarTask=self
                )
            elif "/tv/" in filterData["url"]:
                genres = showScraper.getGenreArray(soup)
                ratings = ["all"]
                URLs = generateTVshowURLs(
                    genres, ratings, platforms, tomatometerScore, audienceScore,
                    limit - addedCount, True
                )
                res =  scrapeTVshows(
                    URLs, tomatometerScore, audienceScore, limit - addedCount, 
                    year=oldestYear, skipURL=filterData["url"], key=key,
                    similarProgress=addedCount, similarTask=self
                )
        for row in res:
            for entry in row:
                # if the last row is full, create a new row
                if len(similarInfo[-1]) == 4:
                    similarInfo.append([entry])
                else:
                    similarInfo[-1].append(entry)
        end = time.time()
        print(f'Time to generate similar recs: {end - start}')
        if key:
            self.update_state(
                state="SUCCESS",
                meta={
                    'result': 'recommendations/' + self.request.id,
                    'key': key,
                    'similarInfo': similarInfo 
                }
            )
        return similarInfo
    except:
        print("Error scraping similar")
        raise