from tkinter.messagebox import showinfo
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
    baseURL = "https://www.rottentomatoes.com"
    desiredInfoCategories = [
        "Rating:", "Genre:", "Original Language:", "Release Date (Theaters):",
        "Release Date (Streaming):", "Runtime:", "Director:", "Producer:", "Writer:"
    ]
    # Format platforms for frontend
    platformDict = {
        "amazon-prime-video-us": "Amazon Prime Video",
        "itunes": "iTunes",
        "apple-tv-plus-us": "Apple TV+",
        "disney-plus-us": "Disney+",
        "hbo-max": "HBO Max",
        "hulu": "Hulu",
        "netflix": "Netflix",
        "paramount-plus-us": "Paramount+",
        "peacock": "Peacock",
        "vudu": "Vudu"
    }

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

            url = baseURL + movie["href"]
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
                    platformList.append("In Theaters")
                else:
                    platformList.append(platformDict[platform["affiliate"]])
            platformString = ", ".join(platformList)
            movieInfoDict["platforms"] = platformString

            # Cast
            castDict = {}
            cast = movieSoup.find_all(
                "a",
                attrs={"data-qa": "cast-crew-item-link"},
                limit=6
            )
            for actor in cast:
                actorURL = baseURL + actor["href"].strip()
                actorName = actor.contents[1].text.strip()
                castDict[actorName] = actorURL
            movieInfoDict["cast"] = castDict

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
                    formattedInfo = formattedInfo.replace(",", ", ")
                elif info.text == desiredInfoCategories[2] or \
                    info.text == desiredInfoCategories[5]:
                    formattedInfo = info.next_sibling.next_sibling.text.strip()
                elif info.text == desiredInfoCategories[3] or \
                    info.text == desiredInfoCategories[4]:
                    date = info.next_sibling.next_sibling.text.split()
                    formattedInfo = date[0] + " " + date[1] + " " + date[2]
                elif info.text == desiredInfoCategories[6]:
                    directorDict = {}
                    sibling = info.next_sibling.next_sibling
                    for director in sibling.contents:
                        if director.name != "a":
                            continue
                        directorName = director.text.strip()
                        directorURL = baseURL + director["href"]
                        directorDict[directorName] = directorURL
                    movieInfoDict["director"] = directorDict
                elif info.text == desiredInfoCategories[7]:
                    producerDict = {}
                    sibling = info.next_sibling.next_sibling
                    for producer in sibling.contents:
                        if producer.name != "a":
                            continue
                        producerName = producer.text.strip()
                        producerURL = baseURL + producer["href"]
                        producerDict[producerName] = producerURL
                    movieInfoDict["producer"] = producerDict
                elif info.text == desiredInfoCategories[8]:
                    writerDict = {}
                    sibling = info.next_sibling.next_sibling
                    for writer in sibling.contents:
                        if writer.name != "a":
                            continue
                        writerName = writer.text.strip()
                        writerURL = baseURL + writer["href"]
                        writerDict[writerName] = writerURL
                    movieInfoDict["writer"] = writerDict
                else:
                    continue
                
                if info.text != desiredInfoCategories[6] and \
                    info.text != desiredInfoCategories[7] and \
                    info.text != desiredInfoCategories[8]:
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

    # Format platforms for frontend
    platformDict = {
        "amazon-prime-video-us": "Amazon Prime Video",
        "itunes": "iTunes",
        "apple-tv-plus-us": "Apple TV+",
        "disney-plus-us": "Disney+",
        "hbo-max": "HBO Max",
        "hulu": "Hulu",
        "netflix": "Netflix",
        "paramount-plus-us": "Paramount+",
        "peacock": "Peacock",
        "vudu": "Vudu"
    }

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
                platformList.append(platformDict[platform["affiliate"]])
            platformString = ", ".join(platformList)
            tvShowInfoDict["platforms"] = platformString

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

            creatorsDict = {}
            creators = tvShowSoup.find_all(
                "a",
                attrs={"data-qa": "creator"}
            )
            for creator in creators:
                creatorName = creator.text.strip()
                creatorURL = baseURL + creator["href"]
                creatorsDict[creatorName] = creatorURL
            tvShowInfoDict["creators"] = creatorsDict
            
            producersDict = {}
            producers = tvShowSoup.find_all(
                "a",
                attrs={"data-qa": "series-details-producer"},
                limit=6
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

def scrapeActor(filterData):
    baseURL = "https://www.rottentomatoes.com"
    count = 0
    filmographyInfo = [[]]

    # Format platforms for frontend
    platformDict = {
        "amazon-prime-video-us": "Amazon Prime Video",
        "itunes": "iTunes",
        "apple-tv-plus-us": "Apple TV+",
        "disney-plus-us": "Disney+",
        "hbo-max": "HBO Max",
        "hulu": "Hulu",
        "netflix": "Netflix",
        "paramount-plus-us": "Paramount+",
        "peacock": "Peacock",
        "vudu": "Vudu"
    }

    html_text = requests.get(url=filterData["actorURL"]).text
    soup = BeautifulSoup(html_text, "lxml")

    # If URL is invalid, return None
    main_page_content = soup.find("div", attrs={"id": "main-page-content"})
    if main_page_content.contents[1].contents[1].text.strip() == "404 - Not Found":
        return None

    # Scrape movies
    if filterData["category"] == "movie":
        movies = soup.find_all("tr", attrs={
            "data-qa": "celebrity-filmography-movies-trow"
        })
        for movie in movies:
            if count == filterData["limit"]:
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
            
            # Filter by box office
            if boxOffice // 1000000 < filterData["boxOffice"]:
                continue
                
            # Filter by year
            if year < filterData["oldestYear"]:
                continue

            # Search movie page
            moviePageURL = baseURL + movie.contents[5].contents[1]["href"]
            movie_html_text = requests.get(url=moviePageURL).text
            movieSoup = BeautifulSoup(movie_html_text, "lxml")

            movieInfoDict = {
                "type": "movie",
                "name": name,
                "audienceScore": audienceScore,
                "criticsScore": tomatometerScore,
                "url": moviePageURL,
                "role": role,
                "boxOffice": "$" + str(boxOffice // 1000000) + "M",
                "year": year
            }
            
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

            # If none of the movie's platforms match the filter, skip
            platformFlag = True if "all" in filterData["platforms"] else False

            for platform in availablePlatforms:
                if platform["affiliate"] in filterData["platforms"]:
                    platformFlag = True

                if platform["affiliate"] == "showtimes":
                    platformList.append("In Theaters")
                else:
                    platformList.append(platformDict[platform["affiliate"]])

            if not platformFlag:
                continue
                
            platformString = ", ".join(platformList)
            movieInfoDict["platforms"] = platformString

            # Additional information (rating, genre, original language, runtime)
            additionalInfo = movieSoup.find_all(
                "div", 
                attrs={"data-qa": "movie-info-item-label"}
            )

            # If a movie doesn't pass the rating filter, skip it
            ratingFlag = False

            # If a movie doesn't pass the genre filter, skip it
            genreFlag = False

            for info in additionalInfo:
                # Filter and format data depending on category
                if info.text == "Rating:":
                    rating = info.next_sibling.next_sibling.text.split()[0]
                    if "all" in filterData["ratings"] or rating in filterData["ratings"]:
                        ratingFlag = True
                    movieInfoDict["rating"] = rating

                elif info.text == "Genre:":
                    genreString = info.next_sibling.next_sibling.text.strip()
                    genreString = genreString.replace("\n", "").replace(" ", "")
                    if "all" in filterData["genres"]:
                        genreFlag = True
                        genreString = genreString.replace(",", ", ").replace("&", " & ")
                        movieInfoDict["genres"] = genreString
                    else:
                        genreList = genreString.split(",")
                        for genre in genreList:
                            if genre in filterData["genres"]:
                                genreFlag = True
                        genreString = genreString.replace(",", ", ").replace("&", " & ")
                        movieInfoDict["genres"] = genreString

                elif info.text == "Original Language:":
                    movieInfoDict["language"] = info.next_sibling.next_sibling.text.strip()
                elif info.text == "Runtime:":
                    movieInfoDict["runtime"] = info.next_sibling.next_sibling.text.strip()   
                else:
                    continue

            if ratingFlag and genreFlag:
                # if the last row is full, create a new row
                if len(filmographyInfo[-1]) == 4:
                    filmographyInfo.append([movieInfoDict])
                else:
                    filmographyInfo[-1].append(movieInfoDict)
                count += 1


    # Scrape TV shows
    elif filterData["category"] == "tv":
        filterData["genres"] = list(map(lambda x: x.replace("&", " ").replace("-F", " f"), filterData["genres"]))
        tvShows = soup.find_all("tr", attrs={
            "data-qa": "celebrity-filmography-tv-trow"
        })
        for tvShow in tvShows:
            if count == filterData["limit"]:
                break
            name = tvShow["data-title"]
            print(name) # DEBUGGING: Print name
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
            showPageURL = baseURL + tvShow.contents[5].contents[1]["href"]
            show_html_text = requests.get(url=showPageURL).text
            showSoup = BeautifulSoup(show_html_text, "lxml")

            showInfoDict = {
                "type": "tv",
                "name": name,
                "audienceScore": audienceScore,
                "criticsScore": tomatometerScore,
                "url": showPageURL,
                "role": role,
                "years": yearString
            }
            
            # Genre
            genre = showSoup.find(
                "td", 
                attrs={"data-qa": "series-details-genre"}
            )
            if genre is not None:
                genre = genre.text
                if "all" not in filterData["genres"] and genre not in filterData["genres"]:
                    continue
                showInfoDict["genre"] = genre

            # Available streaming platforms
            availablePlatforms = showSoup.find_all("where-to-watch-meta")
            platformList = []

            # If none of the show's platforms match the filter, skip
            platformFlag = True if "all" in filterData["platforms"] else False

            for platform in availablePlatforms:
                if platform["affiliate"] in filterData["platforms"]:
                    platformFlag = True
                
                platformList.append(platformDict[platform["affiliate"]])

            if not platformFlag:
                continue
                
            platformString = ", ".join(platformList)
            showInfoDict["platforms"] = platformString

            # TV network
            network = showSoup.find(
                "td", 
                attrs={"data-qa": "series-details-network"}
            )
            if network is not None:
                showInfoDict["network"] = network.text
            
            # show poster image
            posterImage = showSoup.find(
                "img",
                attrs={"class": re.compile("posterImage")}
            )
            if posterImage is None:
                showInfoDict["posterImage"] = "../../static/blank_poster.png"
            elif posterImage.has_attr("data-src"):
                showInfoDict["posterImage"] = posterImage["data-src"]
            else:
                showInfoDict["posterImage"] = "../../static/blank_poster.png"

            # if the last row is full, create a new row
            if len(filmographyInfo[-1]) == 4:
                filmographyInfo.append([showInfoDict])
            else:
                filmographyInfo[-1].append(showInfoDict)
            count += 1


    print(f"Total count: {count}")
    return filmographyInfo




