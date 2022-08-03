# Helper file that modularizes movie scraping
# TODO: modularize some of the filtering steps
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

def setCast(movieSoup, movieInfoDict):
    castDict = {}
    cast = movieSoup.find_all(
        "a",
        attrs={"data-qa": "cast-crew-item-link"},
        limit=6
    )
    for actor in cast:
        actorURL = BASE_URL + actor["href"].strip()
        actorName = actor.contents[1].text.strip()
        castDict[actorName] = actorURL
    movieInfoDict["cast"] = castDict

def setRating(info, movieInfoDict):
    rating = info.next_sibling.next_sibling.text.split()[0]
    movieInfoDict["rating"] = rating

def setGenres(info, movieInfoDict):
    genreString = info.next_sibling.next_sibling.text.strip().replace(" ", "")\
    .replace("\n", "").replace(",", ", ")
    movieInfoDict["genres"] = genreString

def setLanguage(info, movieInfoDict):
    language = info.next_sibling.next_sibling.text.strip()
    movieInfoDict["language"] = language

def setDate(info, movieInfoDict, type):
    date = info.next_sibling.next_sibling.text.split()
    formattedDate = date[0] + " " + date[1] + " " + date[2]
    movieInfoDict[type] = formattedDate

def setRuntime(info, movieInfoDict):
    runtime = info.next_sibling.next_sibling.text.strip()
    movieInfoDict["runtime"] = runtime

def setDirectors(info, movieInfoDict):
    directorDict = {}
    directorTag = info.next_sibling.next_sibling
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
    for writer in writerTag.contents:
        if writer.name != "a":
            continue
        writerName = writer.text.strip()
        writerURL = BASE_URL + writer["href"]
        writerDict[writerName] = writerURL
    movieInfoDict["writers"] = writerDict