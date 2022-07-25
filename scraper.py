import requests
from bs4 import BeautifulSoup
import json
import re

def generateURLs(type, genres, ratings, platforms, tomatometerScore, audienceScore):
    URLs = []
    if type == "MOVIE":
        theatersURL = "https://www.rottentomatoes.com/browse/movies_in_theaters/"
        homeURL = "https://www.rottentomatoes.com/browse/movies_at_home/"

        if int(audienceScore) >= 60:   
            audienceString = "audience:upright~"
        else:
            audienceString = "audience:spilled~"

        if int(tomatometerScore) >= 60:
            tomatometerString = "critics:fresh~"
        else:
            tomatometerString = "critics:rotten~"


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
            URLs.append(
                theatersURL + audienceString + tomatometerString + genreString\
                + ratingString + "sort:popular?page=1"
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

            URLs.append(
                homeURL + audienceString + tomatometerString + platformString\
                + genreString + ratingString + "sort:popular?page=1"
            )
        print(URLs)
        return URLs

def scrapeMovies(URLs, tomatometerScore, audienceScore, recommendationsNumber):
    # array of row arrays; each row array contains up to 4 dictionaries/movies
    movieInfo = [[]]
    movieCount = 0
    desiredInfoCategories = [
        "Rating:", "Genre:", "Original Language:", "Release Date (Theaters):",
        "Release Date (Streaming):", "Runtime:"
    ]
    for url in URLs:
        html_text = requests.get(
            url=url
        ).text
        moviePageSoup = BeautifulSoup(html_text, "lxml")
        movies = moviePageSoup.find_all(
            "a", 
            attrs={"href": re.compile("/m/"), "data-id": True}, 
            limit=int(recommendationsNumber) // len(URLs)
        )

        for movie in movies:
            url = "https://www.rottentomatoes.com" + movie["href"]
            data = movie.find("div", slot="caption")
            scores = data.contents[1]
            name = data.contents[-2].text.strip()

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

            # TODO:

            # Figure out beforehand how many results we need and how many
            # pages we need to look through, then add to urls
            # -> Add this functionality to the URL scraper

            # Filtering must happen before we parse movie data, e.g.
            # check if the movie fits our paramters, then scrape the rest 
            # of the data

            # skip some entries for randomness

            # Use a dictionary to avoid duplicates



            # After filtering, we need to format data so it's human readable
            # Edits to make:
            # Change platforms, including changing "showtimes" to "in theaters"


    
    # DEBUGGING: Print total number of movies scraped
    print(f"Movie count: {movieCount}")

    return movieInfo