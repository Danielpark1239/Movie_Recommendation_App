import requests
from bs4 import BeautifulSoup
import random
import re

# some repeated code, but hard to modularize since pageString
# depends on the number of URLs already in the list
def generateMovieURLs(
    genres, ratings, platforms, tomatometerScore, audienceScore, limit, popular
):  
    URLs = []
    # RT shows 30 movies per page max
    ENTRIES_PER_PAGE = 30
    # If scores are above a certain threshold, generate more pages to search
    gourmet = True if tomatometerScore >= 75 or audienceScore >= 75 else False
    gourmetPages = tomatometerScore // 10 + audienceScore // 10

    theatersURL = "https://www.rottentomatoes.com/browse/movies_in_theaters/"
    homeURL = "https://www.rottentomatoes.com/browse/movies_at_home/"
        
    audienceStrings = ["audience:upright~"]
    if audienceScore < 60:   
        audienceStrings.append("audience:spilled~")

    tomatometerStrings = ["critics:fresh~"]
    if tomatometerScore < 60:
        tomatometerStrings.append("critics:rotten~")

    # number of combinations of score strings
    scoreCombinations = len(audienceStrings) * len(tomatometerStrings)

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

    # Generate from theatersURL
    if "all" in platforms or "showtimes" in platforms:
        if "showtimes" in platforms:
            platforms.remove("showtimes")

    # Determine the number of pages we need
    pageString = "sort:popular?page="

    if "all" in platforms or len(platforms) > 0:
        if gourmet:
            pageString += str(limit // (ENTRIES_PER_PAGE * scoreCombinations) + gourmetPages)
        else:
            pageString += str(limit // (ENTRIES_PER_PAGE * scoreCombinations) + 1)
    else:
        if gourmet:
            pageString +=  str((2 * limit) // (ENTRIES_PER_PAGE * scoreCombinations)+ gourmetPages)
        else:
            pageString += str(limit // (ENTRIES_PER_PAGE * scoreCombinations) + 1)

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
            # Mapping from platform to correct URL representation
            platformDict = {
                "amazon-prime-video-us": "amazon_prime",
                "itunes": "apple_tv",
                "apple-tv-plus-us": "apple_tv_plus",
                "disney-plus-us": "disney_plus",
                "hbo-max": "hbo_max",
                "hulu": "hulu",
                "netflix": "netflix",
                "paramount-plus-us": "paramount_plus",
                "peacock": "peacock",
                "vudu": "vudu"
            }
            platforms = [platformDict[platform] for platform in platforms]
            platformString = "affiliates:" + ",".join(platforms) + "~"
            
        pageString = "sort:popular?page="
        if len(URLs) > 0:
            if gourmet:
                pageString += str(limit // (ENTRIES_PER_PAGE * scoreCombinations) + gourmetPages)
            else:
                pageString += str(limit // (ENTRIES_PER_PAGE * scoreCombinations) + 1)
        else:
            if gourmet:
                pageString +=  str((2 * limit) // (ENTRIES_PER_PAGE * scoreCombinations) + gourmetPages)
            else:
                pageString +=  str((2 * limit) // (ENTRIES_PER_PAGE * scoreCombinations) + 1)

        for audienceString in audienceStrings:
            for tomatometerString in tomatometerStrings:
                URLs.append(
                    homeURL + audienceString + tomatometerString + platformString\
                    + genreString + ratingString + pageString
                )
        if not popular:
            random.shuffle(URLs)
        print(URLs)
        return URLs

def generateTVshowURLs(
    genres, ratings, platforms, tomatometerScore, audienceScore, limit, popular
):
    URLs = []
    ENTRIES_PER_PAGE = 30
    gourmet = True if tomatometerScore >= 75 or audienceScore >= 75 else False
    gourmetPages = tomatometerScore // 10 + audienceScore // 10

    baseURL = "https://www.rottentomatoes.com/browse/tv_series_browse/"

    audienceStrings = ["audience:upright~"]
    if audienceScore < 60:   
        audienceStrings.append("audience:spilled~")

    tomatometerStrings = ["critics:fresh~"]
    if tomatometerScore < 60:
        tomatometerStrings.append("critics:rotten~")
    scoreCombinations = len(audienceStrings) * len(tomatometerStrings)
    
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
        platformDict = {
                "amazon-prime-video-us": "amazon_prime",
                "itunes": "apple_tv",
                "apple-tv-plus-us": "apple_tv_plus",
                "disney-plus-us": "disney_plus",
                "hbo-max": "hbo_max",
                "hulu": "hulu",
                "netflix": "netflix",
                "paramount-plus-us": "paramount_plus",
                "peacock": "peacock",
                "vudu": "vudu"
            }
        platforms = [platformDict[platform] for platform in platforms]
        platformString = "affiliates:" + ",".join(platforms) + "~"
    
    pageString = "sort:popular?page="
    if gourmet:
        pageString +=  str((2 * limit) // (ENTRIES_PER_PAGE * scoreCombinations) + gourmetPages)
    else:
        pageString +=  str((2 * limit) // (ENTRIES_PER_PAGE * scoreCombinations) + 1)

    for audienceString in audienceStrings:
        for tomatometerString in tomatometerStrings:
            URLs.append(
                baseURL + audienceString + tomatometerString + platformString\
                + genreString + ratingString + pageString
            )
    if not popular:
        random.shuffle(URLs)
    print(URLs)
    return URLs

def scrapeMovies(URLs, tomatometerScore, audienceScore, limit):
    # array of row arrays; each row array contains up to 4 dictionaries/movies
    movieInfo = [[]]
    movieCount = 0
    movieDict = {} # Keys contain movie names; used to avoid duplicates
    useRandom = True if tomatometerScore <= 75 and audienceScore <= 75 else False
    maxLimit = 50
    desiredInfoCategories = [
        "Rating:", "Genre:", "Original Language:", "Release Date (Theaters):",
        "Release Date (Streaming):", "Runtime:"
    ]
    for url in URLs:
        if movieCount == limit:
            break

        html_text = requests.get(
            url=url
        ).text
        moviePageSoup = BeautifulSoup(html_text, "lxml")

        # Specify a limit if we have more than 2 URLs to search
        if len(URLs) > 2:
            movies = moviePageSoup.find_all(
                "a", 
                attrs={"href": re.compile("/m/"), "data-id": True}, 
                limit=(limit // len(URLs)) + (maxLimit // 2 * len(URLs))
            )
        else:
            movies = moviePageSoup.find_all(
                "a", 
                attrs={"href": re.compile("/m/"), "data-id": True}, 
            )


        for movie in movies:
            if movieCount == limit:
                break
            
            # 80% chance of movie being added to recommendations
            # if scores are below 80
            # --> Users get different movies each time for the same inputs
            if useRandom:
                randomInt = random.randint(0, 4)
                if randomInt == 0:
                    continue

            url = "https://www.rottentomatoes.com" + movie["href"]
            data = movie.find("div", slot="caption")
            scores = data.contents[1]

            # Filter based on scores
            if scores["audiencescore"] == "" or int(scores["audiencescore"]) < audienceScore:
                continue
            if scores["criticsscore"] == "" or int(scores["criticsscore"]) < tomatometerScore:
                continue

            name = data.contents[-2].text.strip()
            
            # Avoid duplicates
            if name in movieDict:
                continue
            else:
                movieDict[name] = True

            movieInfoDict = {
                "name": name,
                "audienceScore": scores["audiencescore"],
                "criticsScore": scores["criticsscore"],
                "url": url
            }

            # Get additional data about the movie by looking at its page
            movie_html_text = requests.get(url).text
            movieSoup = BeautifulSoup(movie_html_text, "lxml")
            
            # Movie poster image
            print(name) # DEBUGGING: Print name
            posterImage = movieSoup.find(
                "img",
                attrs={"class": re.compile("posterImage")}
            )
            if posterImage.has_attr("data-src"):
                movieInfoDict["posterImage"] = posterImage["data-src"]
            else:
                movieInfoDict["posterImage"] = "../../static/blank_poster.png"

            # Available streaming platforms
            availablePlatforms = movieSoup.find_all("where-to-watch-meta")
            platformList = []
            for platform in availablePlatforms:
                if platform["affiliate"] == "showtimes":
                    platformList.append("in-theaters")
                else:
                    platformList.append(platform["affiliate"])
            movieInfoDict["platforms"] = platformList

            # Additional information (rating, genre, etc.)
            additionalInfo = movieSoup.find_all(
                "div", 
                attrs={"data-qa": "movie-info-item-label"}
            )

            for info in additionalInfo:
                # Format metadata depending on info category
                if info.text == desiredInfoCategories[0]:
                    formattedInfo = info.next_sibling.next_sibling.text.split()[0]
                elif info.text == desiredInfoCategories[1]:
                    formattedInfo = info.next_sibling.next_sibling.text.strip()
                    formattedInfo = formattedInfo.replace(" ", "").replace("\n", "")
                    formattedInfo = formattedInfo.split(",")
                elif info.text == desiredInfoCategories[2] or \
                    info.text == desiredInfoCategories[5]:
                    formattedInfo = info.next_sibling.next_sibling.text.strip()
                elif info.text == desiredInfoCategories[3] or \
                    info.text == desiredInfoCategories[4]:
                    date = info.next_sibling.next_sibling.text.split()
                    formattedInfo = date[0] + " " + date[1] + " " + date[2]
                else:
                    continue
                movieInfoDict[info.text[0:-1].lower()] = formattedInfo
            
            # if the last row is full, create a new row
            if len(movieInfo[-1]) == 4:
                movieInfo.append([movieInfoDict])
            else:
                movieInfo[-1].append(movieInfoDict)

            movieCount += 1
    
    # DEBUGGING: Print total number of movies scraped
    print(f"Movie count: {movieCount}")

    return movieInfo

def scrapeTVshows(URLs, tomatometerScore, audienceScore, limit):
    # array of row arrays; each row array contains up to 4 dictionaries/shows
    tvShowInfo = [[]]
    tvShowCount = 0
    tvShowDict = {} # Keys contain tv show names; used to avoid duplicates
    useRandom = True if tomatometerScore <= 75 and audienceScore <= 75 else False
    maxLimit = 50

    baseURL = "https://www.rottentomatoes.com"

    for url in URLs:
        if tvShowCount == limit:
            break

        html_text = requests.get(
            url=url
        ).text
        tvShowPageSoup = BeautifulSoup(html_text, "lxml")

        # Specify a limit if we have more than 2 URLs to search
        if len(URLs) > 2:
            tvShows = tvShowPageSoup.find_all(
                "a", 
                attrs={"href": re.compile("/tv/"), "data-id": True}, 
                limit=(limit // len(URLs)) + (maxLimit // 2 * len(URLs))
            )
        else:
            tvShows = tvShowPageSoup.find_all(
                "a", 
                attrs={"href": re.compile("/tv/"), "data-id": True}, 
            )


        for tvShow in tvShows:
            if tvShowCount == limit:
                break
            
            if useRandom: # 80% chance of show being selected
                randomInt = random.randint(0, 4)
                if randomInt == 0:
                    continue

            url = baseURL + tvShow["href"]
            data = tvShow.find("div", slot="caption")
            scores = data.contents[1]

            # Filter based on scores
            if scores["audiencescore"] == "" or int(scores["audiencescore"]) < audienceScore:
                continue
            if scores["criticsscore"] == "" or int(scores["criticsscore"]) < tomatometerScore:
                continue

            name = data.contents[3].text.strip()
            
            # Avoid duplicates
            if name in tvShowDict:
                continue
            else:
                tvShowDict[name] = True

            tvShowInfoDict = {
                "name": name,
                "audienceScore": scores["audiencescore"],
                "criticsScore": scores["criticsscore"],
                "url": url
            }

            # Get additional data about the show by looking at its page
            tvshow_html_text = requests.get(url).text
            tvShowSoup = BeautifulSoup(tvshow_html_text, "lxml")
            
            # show poster image
            print(name)
            posterImage = tvShowSoup.find(
                "img",
                attrs={"class": re.compile("posterImage")}
            )
            if posterImage.has_attr("data-src"):
                tvShowInfoDict["posterImage"] = posterImage["data-src"]
            else:
                tvShowInfoDict["posterImage"] = "../../static/blank_poster.png"

            # Available streaming platforms
            availablePlatforms = tvShowSoup.find_all("where-to-watch-meta")
            platformList = []
            for platform in availablePlatforms:
                platformList.append(platform["affiliate"])
            tvShowInfoDict["platforms"] = platformList

            # Additional information
            network = tvShowSoup.find(
                "td", 
                attrs={"data-qa": "series-details-network"}
            )
            if network is not None:
                tvShowInfoDict["network"] = network.text
            
            premiereDate = tvShowSoup.find(
                "td", 
                attrs={"data-qa": "series-details-premiere-date"}
            )
            if premiereDate is not None:
                tvShowInfoDict["premiereDate"] = premiereDate.text
            
            genre = tvShowSoup.find(
                "td", 
                attrs={"data-qa": "series-details-genre"}
            )
            if genre is not None:
                tvShowInfoDict["genre"] = genre.text
            
            producersDict = {}
            producers = tvShowSoup.find_all(
                "a",
                attrs={"data-qa": "series-details-producer"}
            )
            for producer in producers:
                producerName = producer.text.strip()
                producerURL = baseURL + producer["href"]
                producersDict[producerName] = producerURL
            tvShowInfoDict["producers"] = producersDict

            castDict = {}
            cast = tvShowSoup.find_all(
                "a",
                attrs={"data-qa": "cast-member"}
            )
            for actor in cast:
                actorName = actor.text.strip()
                actorURL = baseURL + actor["href"]
                castDict[actorName] = actorURL
            tvShowInfoDict["cast"] = castDict

            # if the last row is full, create a new row
            if len(tvShowInfo[-1]) == 4:
                tvShowInfo.append([tvShowInfoDict])
            else:
                tvShowInfo[-1].append(tvShowInfoDict)

            tvShowCount += 1
    
    # DEBUGGING: Print total number of TV shows scraped
    print(f"TV show count: {tvShowCount}")

    return tvShowInfo

