from flask import Flask, render_template, request
import scraper

app = Flask(__name__)

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

@app.route('/movies/', methods=['GET'])
def movies():
    return render_template('movies.html')

@app.route('/movies/recommendations/', methods=['POST'])
def movieRecommendations():
    formData = request.form
    genres = formData.getlist("genres")
    ratings = formData.getlist("ratings")
    platforms = formData.getlist("platforms")
    tomatometerScore = int(formData["tomatometerSlider"])
    audienceScore = int(formData["audienceSlider"])
    limit = int(formData["limit"])
    popular = True if "popular" in formData else False

    URLs = scraper.generateURLs(
        "MOVIE", genres, ratings, platforms, tomatometerScore, audienceScore, limit, popular
    )
    movieInfo = scraper.scrapeMovies(
        URLs, tomatometerScore, audienceScore, limit
    )

    return render_template("movieRecommendations.html", movieInfo=movieInfo)