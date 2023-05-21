# Helper file that modularizes movie scraping
import re
from constants import *

# For a given movieSoup, return the name as a string
def getName(movieSoup):
    name = movieSoup.find(
        "h1",
        attrs={
            "data-qa": "score-panel-title"
        }
    )
    if name is None or name.text.strip() == "":
        return None
    return name.text.strip()

# For a given movieSoup and movieInfoDict, set the poster image
# in the movieInfoDict
def setPosterImage(movieSoup, movieInfoDict):
    posterImage = movieSoup.find(
        "tile-dynamic",
        attrs={"class": "thumbnail"}
    ).find("img", recursive=False)
    if posterImage is None:
        movieInfoDict["posterImage"] = BLANK_POSTER
    elif posterImage.has_attr("data-src"):
        imageURL = posterImage["data-src"]
        imageURL = imageURL.replace("/206x305/", "/480x0/")
        movieInfoDict["posterImage"] = imageURL
    elif posterImage.has_attr("src"):
        imageURL = posterImage["src"]
        imageURL = imageURL.replace("/206x305/", "/480x0/")
        movieInfoDict["posterImage"] = imageURL
    else:
        movieInfoDict["posterImage"] = BLANK_POSTER

# For a given movieSoup and movieInfoDict, set the platforms in the 
# movieInfoDict
def setPlatforms(movieSoup, movieInfoDict):
    availablePlatforms = movieSoup.find_all("where-to-watch-meta")
    platformList = []
    for platform in availablePlatforms:
        if platform["affiliate"] in FRONTEND_PLATFORM_DICT:
            platformList.append(
                FRONTEND_PLATFORM_DICT[platform["affiliate"]]
            )
        else:
            platformList.append(platform["affiliate"])
    platformString = ", ".join(platformList)
    movieInfoDict["platforms"] = platformString

# Returns True if at least one of the movie's platforms match the filter,
# and False otherwise
def setPlatformsWithFilter(movieSoup, movieInfoDict, filterList):
    flag = True if "all" in filterList else False
    availablePlatforms = movieSoup.find_all("where-to-watch-meta")
    platformList = []
    for platform in availablePlatforms:
        if platform["affiliate"] in filterList:
            flag = True
        if platform["affiliate"] in FRONTEND_PLATFORM_DICT:
            platformList.append(
                FRONTEND_PLATFORM_DICT[platform["affiliate"]]
            )
        else:
            platformList.append(platform["affiliate"])
    platformString = ", ".join(platformList)
    movieInfoDict["platforms"] = platformString
    return flag

# For a given movieSoup and movieInfoDict, set the cast in the movieInfoDict
def setCast(movieSoup, movieInfoDict):
    castDict = {}
    cast = movieSoup.find_all(
        "a",
        attrs={"data-qa": "cast-crew-item-link"},
        limit=6
    )
    if cast is not None:
        for actor in cast:
            actorURL = BASE_URL + actor["href"].strip()
            actorName = actor.contents[1].text.strip()
            castDict[actorName] = actorURL
        movieInfoDict["cast"] = castDict

def setRating(info, movieInfoDict):
    ratingSpan = info.find_next_sibling("span")
    if ratingSpan is None:
        return
    rating = ratingSpan.text.split()[0]
    if rating is not None:
        movieInfoDict["rating"] = rating

# Returns True if the movie's rating matches the filter, False otherwise
def setRatingWithFilter(info, movieInfoDict, filterList):
    flag = True if "all" in filterList else False
    ratingSpan = info.find_next_sibling("span")
    if ratingSpan is None:
        return False
    rating = ratingSpan.text.split()[0]
    if rating in filterList:
        flag = True
    if rating is not None:
        movieInfoDict["rating"] = rating
    return flag

# Defaults to ["all"] if no rating can be found
def getRatingArray(moviePageSoup):
    metaLabels = moviePageSoup.find_all("div", attrs={
        "class": "meta-label subtle",
        "data-qa": "movie-info-item-label"
    })
    ratingArray = ["all"]
    for metaLabel in metaLabels:
        if metaLabel.text == "Rating:":
            rating = metaLabel.next_sibling.next_sibling.text.strip().split()[0]
            ratingArray = [rating.lower().replace("-", "_")]
            break
    return ratingArray

# For a matching info tag, set the genres in the movieInfoDict
def setGenres(info, movieInfoDict):
    genreString = info.next_sibling.next_sibling.text.strip().replace(" ", "")\
    .replace("\n", "").replace(",", ", ").replace("&", " & ")
    movieInfoDict["genres"] = genreString

# Returns True if at least one of the movie's genres matches the filter, False otherwise
def setGenresWithFilter(info, movieInfoDict, filterList):
    flag = True if "all" in filterList else False
    genreString = info.next_sibling.next_sibling.text.strip().replace("\n", "")\
    .replace(" ", "")
    genreList = genreString.split(",")
    for genre in genreList:
        if genre in filterList:
            flag = True
    genreString = genreString.replace(",", ", ").replace("&", " & ")
    movieInfoDict["genres"] = genreString
    return flag

# Defaults to ["all"] if no genres can be found
def getGenreArray(moviePageSoup):
    genreTag = moviePageSoup.find("div", attrs={
        "class": "meta-value genre",
        "data-qa": "movie-info-item-value"
    })
    if genreTag is None or genreTag.text == "":
        genres = ["all"]
    else:
        genreString = genreTag.text.strip().replace("\n", "").lower().replace(", ", ",")
        genreString = genreString.replace(" & ", "_and_").replace("-", "_").replace("+", "")
        genres = genreString.split(",")
        for i in range(len(genres)):
            genres[i] = genres[i].strip()
            genres[i] = genres[i].replace(" ", "_")
    return genres

# For a matching info tag, set the language in the movieInfoDict
def setLanguage(info, movieInfoDict):
    language = info.next_sibling.next_sibling.text.strip()
    if language is not None:
        movieInfoDict["language"] = language

# For a matching info tag, set the date in the movieInfoDict
def setDate(info, movieInfoDict, type):
    date = info.next_sibling.next_sibling.text.split()
    if date is not None:
        formattedDate = date[0] + " " + date[1] + " " + date[2]
        movieInfoDict[type] = formattedDate

# Returns True if the movie was released on or after a certain year,
# False otherwise (Uses Theaters release Date)
# If no date can be found, returns False
def setDateWithFilter(info, movieInfoDict, oldestYear):
    date = info.next_sibling.next_sibling.text.split()
    if date is None:
        return False
    year = int(date[2])
    if oldestYear > year:
        return False
    formattedDate = date[0] + " " + date[1] + " " + date[2]
    movieInfoDict["theaters"] = formattedDate
    return True

# For a matching info tag, set the runtime in movieInfoDict
def setRuntime(info, movieInfoDict):
    runtime = info.next_sibling.next_sibling.text.strip()
    if runtime is not None:
        movieInfoDict["runtime"] = runtime

# For a matching info tag, set directors in movieInfoDict
def setDirectors(info, movieInfoDict):
    directorDict = {}
    directorTag = info.next_sibling.next_sibling
    if directorTag is not None:
        for director in directorTag.contents:
            if director.name != "a":
                continue
            directorName = director.text.strip()
            directorURL = BASE_URL + director["href"]
            directorDict[directorName] = directorURL
        movieInfoDict["directors"] = directorDict

# For a matching info tag, set producers in movieInfoDict
def setProducers(info, movieInfoDict):
    producerDict = {}
    producerTag = info.next_sibling.next_sibling
    if producerTag is not None:
        for producer in producerTag.contents:
            if producer.name != "a":
                continue
            producerName = producer.text.strip()
            producerURL = BASE_URL + producer["href"]
            producerDict[producerName] = producerURL
        movieInfoDict["producers"] = producerDict

# For a matching info tag, set writers in movieInfoDict
def setWriters(info, movieInfoDict):
    writerDict = {}
    writerTag = info.next_sibling.next_sibling
    if writerTag is not None:
        for writer in writerTag.contents:
            if writer.name != "a":
                continue
            writerName = writer.text.strip()
            writerURL = BASE_URL + writer["href"]
            writerDict[writerName] = writerURL
        movieInfoDict["writers"] = writerDict