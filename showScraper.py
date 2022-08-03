# Helper file that modularizes TV show scraping
# TODO: modularize some of the filtering steps
import re
from constants import *

def setPosterImage(showSoup, showInfoDict):
    posterImage = showSoup.find(
        "img",
        attrs={"class": re.compile("posterImage")}
    )
    if posterImage is None:
        showInfoDict["posterImage"] = BLANK_POSTER
    elif posterImage.has_attr("data-src"):
        showInfoDict["posterImage"] = posterImage["data-src"]
    else:
        showInfoDict["posterImage"] = BLANK_POSTER

def setPlatforms(showSoup, showInfoDict):
    availablePlatforms = showSoup.find_all("where-to-watch-meta")
    platformList = []
    for platform in availablePlatforms:
        platformList.append(FRONTEND_PLATFORM_DICT[platform["affiliate"]])
    platformString = ", ".join(platformList)
    showInfoDict["platforms"] = platformString

def setNetwork(showSoup, showInfoDict):
    network = showSoup.find(
        "td", 
        attrs={"data-qa": "series-details-network"}
    )
    if network is not None:
        showInfoDict["network"] = network.text

def setPremiereDate(showSoup, showInfoDict):
    premiereDate = showSoup.find(
        "td", 
        attrs={"data-qa": "series-details-premiere-date"}
    )
    if premiereDate is not None:
        showInfoDict["premiereDate"] = premiereDate.text

def setGenre(showSoup, showInfoDict):
    genre = showSoup.find(
        "td", 
        attrs={"data-qa": "series-details-genre"}
    )
    if genre is not None:
        showInfoDict["genre"] = genre.text

def setCreators(showSoup, showInfoDict):
    creatorsDict = {}
    creators = showSoup.find_all(
        "a",
        attrs={"data-qa": "creator"}
    )
    for creator in creators:
        creatorName = creator.text.strip()
        creatorURL = BASE_URL + creator["href"]
        creatorsDict[creatorName] = creatorURL
    showInfoDict["creators"] = creatorsDict

def setProducers(showSoup, showInfoDict):
    producersDict = {}
    producers = showSoup.find_all(
        "a",
        attrs={"data-qa": "series-details-producer"},
        limit=6
    )
    for producer in producers:
        producerName = producer.text.strip()
        producerURL = BASE_URL + producer["href"]
        producersDict[producerName] = producerURL
    showInfoDict["producers"] = producersDict

def setCast(showSoup, showInfoDict):
    castDict = {}
    cast = showSoup.find_all(
        "a",
        attrs={"data-qa": "cast-member"}
    )
    for actor in cast:
        actorName = actor.text.strip()
        actorURL = BASE_URL + actor["href"]
        castDict[actorName] = actorURL
    showInfoDict["cast"] = castDict