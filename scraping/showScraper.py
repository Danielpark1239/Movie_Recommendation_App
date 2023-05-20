# Helper file that modularizes TV show scraping
# TODO: modularize some of the filtering steps
import re
from constants import *

# For a given showSoup, return the name as a string
def getName(showSoup):
    name = showSoup.find(
        "h1",
        attrs={
            "data-qa": "score-panel-series-title"
        }
    )
    if name is None or name.text.strip() == "":
        return None
    return name.text.strip()

# For a given showSoup, set the poster image in showInfoDict
def setPosterImage(showSoup, showInfoDict):
    posterImage = showSoup.find(
        "img",
        attrs={"class": re.compile("posterImage")}
    )
    if posterImage is None:
        showInfoDict["posterImage"] = BLANK_POSTER
    elif posterImage.has_attr("data-src"):
        imageURL = posterImage["data-src"]
        imageURL = imageURL.replace("/206x305/", "/480x0/")
        showInfoDict["posterImage"] = imageURL
    elif posterImage.has_attr("src"):
        imageURL = posterImage["src"]
        imageURL = imageURL.replace("/206x305/", "/480x0/")
        showInfoDict["posterImage"] = imageURL
    else:
        showInfoDict["posterImage"] = BLANK_POSTER

# For a given showSoup, set platforms in the showInfoDict
def setPlatforms(showSoup, showInfoDict):
    availablePlatforms = showSoup.find_all("where-to-watch-meta")
    if availablePlatforms is not None:
        platformList = []
        for platform in availablePlatforms:
            if platform["affiliate"] in FRONTEND_PLATFORM_DICT:
                platformList.append(
                    FRONTEND_PLATFORM_DICT[platform["affiliate"]]
                )
            else:
                platformList.append(platform["affiliate"])
        platformString = ", ".join(platformList)
        showInfoDict["platforms"] = platformString

# For a given showSoup, set platforms in the showInfoDict adhering 
# to the filters in filterList
def setPlatformsWithFilter(showSoup, showInfoDict, filterList):
    flag = True if "all" in filterList else False
    availablePlatforms = showSoup.find_all("where-to-watch-meta")
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
    showInfoDict["platforms"] = platformString
    return flag

# For a given showSoup, set the TV network in showInfoDict
def setNetwork(showSoup, showInfoDict):
    network = showSoup.find(
        "td", 
        attrs={"data-qa": "series-details-network"}
    )
    if network is not None:
        showInfoDict["network"] = network.text

# For a given showSoup, set the premiere date in showInfoDict
def setPremiereDate(showSoup, showInfoDict):
    premiereDate = showSoup.find(
        "td", 
        attrs={"data-qa": "series-details-premiere-date"}
    )
    if premiereDate is not None and premiereDate.text != "":
        showInfoDict["premiereDate"] = premiereDate.text

# Returns True if the show premiered on or after a certain year,
# False otherwise. If no date can be found, returns False
def setPremiereDateWithFilter(showSoup, showInfoDict, oldestYear):
    premiereDate = showSoup.find(
        "td", 
        attrs={"data-qa": "series-details-premiere-date"}
    )
    if premiereDate is None or premiereDate.text == "":
        return False
    year = int(premiereDate.text[-4:])
    if year < oldestYear:
        return False
    showInfoDict["premiereDate"] = premiereDate.text
    return True

# For a given showSoup, set the genre in showInfoDict
def setGenre(showSoup, showInfoDict):
    genreTag = showSoup.find(
        "td", 
        attrs={"data-qa": "series-details-genre"}
    )
    if genreTag is not None:
        genre = genreTag.text.strip()

        if genre in TV_TO_FRONTEND_GENRE_DICT:
            showInfoDict["genre"] = TV_TO_FRONTEND_GENRE_DICT[genre]
        else:
            showInfoDict["genre"] = genre

# Returns True if the show's genre matches the filter, False otherwise
def setGenreWithFilter(showSoup, showInfoDict, filterList):
    filterList = list(
        map(
            lambda x: MOVIE_TO_TV_GENRE_DICT[x], filterList
        )
    )

    flag = True if "all" in filterList else False
    genreTag = showSoup.find(
        "td", 
        attrs={"data-qa": "series-details-genre"}
    )
    if genreTag is not None:
        genre = genreTag.text.strip()
        if genre in filterList:
            flag = True
        if genre in TV_TO_FRONTEND_GENRE_DICT:
            showInfoDict["genre"] = TV_TO_FRONTEND_GENRE_DICT[genre]
        else:
            showInfoDict["genre"] = genre
    return flag

# Default to ["all"] if no genre can be found
def getGenreArray(showSoup):
    genreTag = showSoup.find(
        "td", 
        attrs={"data-qa": "series-details-genre"}
    )
    genreArray = ["all"]
    if genreTag is not None and genreTag.text != "":
        genre = genreTag.text.strip()
        print(genre)
        if genre in TV_TO_URL_GENRE_DICT:
            genreArray = [TV_TO_URL_GENRE_DICT[genre]]
    
    return genreArray
       
# For a given showSoup, set the creators in showInfoDict
def setCreators(showSoup, showInfoDict):
    creatorsDict = {}
    creators = showSoup.find_all(
        "a",
        attrs={"data-qa": "creator"}
    )
    if creators is not None:
        for creator in creators:
            creatorName = creator.text.strip()
            creatorURL = BASE_URL + creator["href"]
            creatorsDict[creatorName] = creatorURL
        showInfoDict["creators"] = creatorsDict

# For a given showSoup, set the producers in showInfoDict
def setProducers(showSoup, showInfoDict):
    producersDict = {}
    producers = showSoup.find_all(
        "a",
        attrs={"data-qa": "series-details-producer"},
        limit=6
    )
    if producers is not None:
        for producer in producers:
            producerName = producer.text.strip()
            producerURL = BASE_URL + producer["href"]
            producersDict[producerName] = producerURL
        showInfoDict["producers"] = producersDict

# For a given showSoup, set the cast in showInfoDict
def setCast(showSoup, showInfoDict):
    castDict = {}
    cast = showSoup.find_all(
        "a",
        attrs={"data-qa": "cast-member"}
    )
    if cast is not None:
        for actor in cast:
            actorName = actor.text.strip()
            actorURL = BASE_URL + actor["href"]
            castDict[actorName] = actorURL
        showInfoDict["cast"] = castDict