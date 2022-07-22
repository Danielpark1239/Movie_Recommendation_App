from flask import Flask, render_template, request
import requests
import json
from bs4 import BeautifulSoup
import re

app = Flask(__name__)

# TO DO:
# General movie search: parse data, then add some filters
# General TV show search: parse data, then add some filters

# Director search
# Producer search
# Actor(s) search


@app.route('/')
def index():
    return render_template("index.html")
    
@app.route('/test/', methods=['GET', 'POST'])
def test():
    if request.method == "POST":
        print(request.form.getlist("platform"))
        print(request.form["tomatometerSlider"])
        print(request.form["audienceSlider"])
    return render_template("test.html")

@app.route('/movies/', methods=['GET', 'POST'])
def get_movies():
    if request.method == "POST":
        print(request.form.getlist("genre"))
        print(request.form.getlist("rating"))
        print(request.form.getlist("platform"))
        print(request.form["tomatometerSlider"])
        print(request.form["audienceSlider"])
        print(request.form["recommendationsNumber"])

    html_text = requests.get(
        url="https://www.rottentomatoes.com/browse/movies_at_home/sort:popular?page=1"
    ).text
    moviePageSoup = BeautifulSoup(html_text, "lxml")
    movies = moviePageSoup.find_all(
        "a", 
        attrs={"href": re.compile("/m/"), "data-id": True}, 
        limit=1 # LIMIT IS 5 FOR NOW
    )
    movieInfo = {}

    desiredInfoCategories = [
            "Rating:", "Genre:", "Original Language:", "Release Date (Theaters):",
            "Release Date (Streaming):", "Runtime:"
        ]

    for movie in movies:
        url = "https://www.rottentomatoes.com" + movie["href"]
        data = movie.find("div", slot="caption")
        scores = data.contents[1]
        name = data.contents[-2].text.strip()

        movieInfo[name] = {
            "audienceScore": scores["audiencescore"],
            "criticsScore": scores["criticsscore"],
        }

        # Get additional data about the movie by looking at its page
        movie_html_text = requests.get(url).text
        movieSoup = BeautifulSoup(movie_html_text, "lxml")

        # Available streaming platforms
        availablePlatforms = movieSoup.find_all("where-to-watch-meta")
        platformList = []
        for platform in availablePlatforms:
            platformList.append(platform["affiliate"])
        movieInfo[name]["platforms"] = platformList

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
            elif info.text == desiredInfoCategories[2] or info.text == desiredInfoCategories[5]:
                formattedInfo = info.next_sibling.next_sibling.text.strip()
            elif info.text == desiredInfoCategories[3] or info.text == desiredInfoCategories[4]:
                date = info.next_sibling.next_sibling.text.split()
                formattedInfo = date[0] + " " + date[1] + " " + date[2]
            else:
                continue
            movieInfo[name][info.text[0:-1].lower()] = formattedInfo
   
    return render_template('movies.html', movieInfo=movieInfo)