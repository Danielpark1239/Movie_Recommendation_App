import requests
from bs4 import BeautifulSoup
import random
import re
from constants import *
import movieScraper
import showScraper

# some repeated code, but hard to modularize since pageString
# depends on the number of URLs already in the list
def generateMovieURLs(
    genres, ratings, platforms, tomatometerScore, audienceScore, limit, popular
):  
    URLs = []
    # If scores are above a certain threshold, generate more pages to search
    gourmet = True if tomatometerScore >= GOURMET_THRESHOLD or\
    audienceScore >= GOURMET_THRESHOLD else False
    gourmetPages = tomatometerScore // 10 + audienceScore // 10

    theatersURL = BASE_MOVIE_THEATERS_URL
    homeURL = BASE_MOVIE_HOME_URL
        
    audienceStrings = ["audience:upright~"]
    if audienceScore < FRESH_THRESHOLD:   
        audienceStrings.append("audience:spilled~")

    tomatometerStrings = ["critics:fresh~"]
    if tomatometerScore < FRESH_THRESHOLD:
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
            platforms = [URL_PLATFORM_DICT[platform] for platform in platforms]
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
    gourmet = True if tomatometerScore >= GOURMET_THRESHOLD or\
    audienceScore >= GOURMET_THRESHOLD else False
    gourmetPages = tomatometerScore // 10 + audienceScore // 10

    audienceStrings = ["audience:upright~"]
    if audienceScore < FRESH_THRESHOLD:   
        audienceStrings.append("audience:spilled~")

    tomatometerStrings = ["critics:fresh~"]
    if tomatometerScore < FRESH_THRESHOLD:
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
        platforms = [URL_PLATFORM_DICT[platform] for platform in platforms]
        platformString = "affiliates:" + ",".join(platforms) + "~"
    
    pageString = "sort:popular?page="
    if gourmet:
        pageString +=  str((2 * limit) // (ENTRIES_PER_PAGE * scoreCombinations) + gourmetPages)
    else:
        pageString +=  str((2 * limit) // (ENTRIES_PER_PAGE * scoreCombinations) + 1)

    for audienceString in audienceStrings:
        for tomatometerString in tomatometerStrings:
            URLs.append(
                BASE_TV_URL + audienceString + tomatometerString\
                + platformString + genreString + ratingString + pageString
            )
    if not popular:
        random.shuffle(URLs)
    print(URLs) # DEBUGGING
    return URLs

def scrapeMovies(URLs, tomatometerScore, audienceScore, limit):
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
                limit=(limit // len(URLs)) + (MAX_LIMIT // 2 * len(URLs))
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

            url = BASE_URL + movie["href"]
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
            
            movieScraper.setPosterImage(movieSoup, movieInfoDict)
            movieScraper.setPlatforms(movieSoup, movieInfoDict)
            movieScraper.setCast(movieSoup, movieInfoDict)

            # Additional information (rating, genre, etc.)
            additionalInfo = movieSoup.find_all(
                "div", 
                attrs={"data-qa": "movie-info-item-label"}
            )

            for info in additionalInfo:
                # Set info depending on category
                if info.text == desiredInfoCategories[0]:
                    movieScraper.setRating(info, movieInfoDict)
                elif info.text == desiredInfoCategories[1]:
                    movieScraper.setGenres(info, movieInfoDict)
                elif info.text == desiredInfoCategories[2]:
                    movieScraper.setLanguage(info, movieInfoDict)
                elif info.text == desiredInfoCategories[3]:
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

            # if the last row is full, create a new row
            if len(movieInfo[-1]) == 4:
                movieInfo.append([movieInfoDict])
            else:
                movieInfo[-1].append(movieInfoDict)

            print(name) # DEBUGGING: Print name
            movieCount += 1
    
    # DEBUGGING: Print total number of movies scraped
    print(f"Movie count: {movieCount}")

    return movieInfo

def scrapeTVshows(URLs, tomatometerScore, audienceScore, limit):
    # array of row arrays; each row array contains up to 4 dictionaries/shows
    tvShowInfo = [[]]
    tvShowCount = 0
    tvShowDict = {} # Keys contain tv show names; used to avoid duplicates
    useRandom = True if tomatometerScore <= RANDOM_THRESHOLD and \
    audienceScore <= RANDOM_THRESHOLD else False

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
                limit=(limit // len(URLs)) + (MAX_LIMIT // 2 * len(URLs))
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

            url = BASE_URL + tvShow["href"]
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
            
            showScraper.setPosterImage(tvShowSoup, tvShowInfoDict)
            showScraper.setPlatforms(tvShowSoup, tvShowInfoDict)
            showScraper.setNetwork(tvShowSoup, tvShowInfoDict)
            showScraper.setPremiereDate(tvShowSoup, tvShowInfoDict)
            showScraper.setGenre(tvShowSoup, tvShowInfoDict)
            showScraper.setCreators(tvShowSoup, tvShowInfoDict)
            showScraper.setProducers(tvShowSoup, tvShowInfoDict)
            showScraper.setCast(tvShowSoup, tvShowInfoDict)

            # if the last row is full, create a new row
            if len(tvShowInfo[-1]) == 4:
                tvShowInfo.append([tvShowInfoDict])
            else:
                tvShowInfo[-1].append(tvShowInfoDict)

            print(name) # Debugging
            tvShowCount += 1
    
    # DEBUGGING: Print total number of TV shows scraped
    print(f"TV show count: {tvShowCount}")

    return tvShowInfo

def scrapeActor(filterData):
    count = 0
    filmographyInfo = [[]]

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
            moviePageURL = BASE_URL + movie.contents[5].contents[1]["href"]
            movie_html_text = requests.get(url=moviePageURL).text
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
                "div", 
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

            # if the last row is full, create a new row
            if len(filmographyInfo[-1]) == 4:
                filmographyInfo.append([movieInfoDict])
            else:
                filmographyInfo[-1].append(movieInfoDict)

            print(name) # DEBUGGING: Print name
            count += 1


    # Scrape TV shows
    elif filterData["category"] == "tv":
        tvShows = soup.find_all("tr", attrs={
            "data-qa": "celebrity-filmography-tv-trow"
        })
        for tvShow in tvShows:
            if count == filterData["limit"]:
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
            show_html_text = requests.get(url=showPageURL).text
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

            # if the last row is full, create a new row
            if len(filmographyInfo[-1]) == 4:
                filmographyInfo.append([showInfoDict])
            else:
                filmographyInfo[-1].append(showInfoDict)

            print(name) # DEBUGGING: Print name
            count += 1

    # Debugging: print count
    print(f"Total count: {count}")
    return filmographyInfo

def scrapeDirectorProducer(filterData, type):
    count = 0
    filmographyInfo = [[]]

    html_text = requests.get(url=filterData["url"]).text
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
            movie_html_text = requests.get(url=moviePageURL).text
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

            # if the last row is full, create a new row
            if len(filmographyInfo[-1]) == 4:
                filmographyInfo.append([movieInfoDict])
            else:
                filmographyInfo[-1].append(movieInfoDict)

            print(name) # DEBUGGING: Print name
            count += 1


    # Scrape TV shows
    elif filterData["category"] == "tv":
        tvShows = soup.find_all("tr", attrs={
            "data-qa": "celebrity-filmography-tv-trow"
        })
        for tvShow in tvShows:
            if count == filterData["limit"]:
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
            show_html_text = requests.get(url=showPageURL).text
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

            # if the last row is full, create a new row
            if len(filmographyInfo[-1]) == 4:
                filmographyInfo.append([showInfoDict])
            else:
                filmographyInfo[-1].append(showInfoDict)
            
            print(name) # DEBUGGING: Print name
            count += 1

    # Debugging
    print(f"Total count: {count}")
    return filmographyInfo


