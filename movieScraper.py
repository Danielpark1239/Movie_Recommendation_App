# Helper file that modularizes movie scraping
import re
from constants import *

def setPosterImage(movieSoup, movieInfoDict):
    posterImage = movieSoup.find(
        "img",
         attrs={"class": re.compile("posterImage")}
    )
    if posterImage is None:
        movieInfoDict["posterImage"] = BLANK_POSTER
    elif posterImage.has_attr("data-src"):
        movieInfoDict["posterImage"] = posterImage["data-src"]
    else:
        movieInfoDict["posterImage"] = BLANK_POSTER

def setPlatforms(movieSoup, movieInfoDict):
    availablePlatforms = movieSoup.find_all("where-to-watch-meta")
    platformList = []
    for platform in availablePlatforms:
        platformList.append(FRONTEND_PLATFORM_DICT[platform["affiliate"]])
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
        platformList.append(FRONTEND_PLATFORM_DICT[platform["affiliate"]])
    platformString = ", ".join(platformList)
    movieInfoDict["platforms"] = platformString
    return flag

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
    rating = info.next_sibling.next_sibling.text.split()[0]
    if rating is not None:
        movieInfoDict["rating"] = rating

# Returns True if the movie's rating matches the filter, False otherwise
def setRatingWithFilter(info, movieInfoDict, filterList):
    flag = True if "all" in filterList else False
    rating = info.next_sibling.next_sibling.text.split()[0]
    if rating in filterList:
        flag = True

    if rating is not None:
        movieInfoDict["rating"] = rating
    return flag

def setGenres(info, movieInfoDict):
    genreString = info.next_sibling.next_sibling.text.strip().replace(" ", "")\
    .replace("\n", "").replace(",", ", ")
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

def setLanguage(info, movieInfoDict):
    language = info.next_sibling.next_sibling.text.strip()
    if language is not None:
        movieInfoDict["language"] = language

def setDate(info, movieInfoDict, type):
    date = info.next_sibling.next_sibling.text.split()
    if date is not None:
        formattedDate = date[0] + " " + date[1] + " " + date[2]
        movieInfoDict[type] = formattedDate

def setRuntime(info, movieInfoDict):
    runtime = info.next_sibling.next_sibling.text.strip()
    if runtime is not None:
        movieInfoDict["runtime"] = runtime

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
        movieInfoDict["director"] = directorDict

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