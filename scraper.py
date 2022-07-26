import requests
from bs4 import BeautifulSoup
import random
import re

def generateURLs(
    type, genres, ratings, platforms, tomatometerScore, audienceScore, limit
):  
    URLs = []
    # RT shows 30 movies per page max
    ENTRIES_PER_PAGE = 30
    if type == "MOVIE":
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
            # We scrape through double the number of entries we need
            pageString = "sort:popular?page="

            if "all" in platforms or len(platforms) > 0:
                pageString += str(limit // (ENTRIES_PER_PAGE * scoreCombinations) + 1)
            else:
                pageString +=  str((2 * limit) // (ENTRIES_PER_PAGE * scoreCombinations)+ 1)

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
                pageString += str(limit // (ENTRIES_PER_PAGE * scoreCombinations) + 1)
            else:
                pageString +=  str((2 * limit) // (ENTRIES_PER_PAGE * scoreCombinations)+ 1)

            for audienceString in audienceStrings:
                for tomatometerString in tomatometerStrings:
                    URLs.append(
                        homeURL + audienceString + tomatometerString + platformString\
                        + genreString + ratingString + pageString
                    )
        print(URLs)
        return URLs

def scrapeMovies(URLs, tomatometerScore, audienceScore, limit):
    # array of row arrays; each row array contains up to 4 dictionaries/movies
    movieInfo = [[]]
    movieCount = 0
    movieDict = {} # Keys contain movie names; used to avoid duplicates
    useRandom = True if tomatometerScore <= 80 and audienceScore <= 80 else False
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
            if int(scores["audiencescore"]) < audienceScore:
                continue
            if int(scores["criticsscore"]) < tomatometerScore:
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
            print(name)
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