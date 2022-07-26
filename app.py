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
  
    genres = request.form.getlist("genres")
    ratings = request.form.getlist("ratings")
    platforms = request.form.getlist("platforms")
    tomatometerScore = int(request.form["tomatometerSlider"])
    audienceScore = int(request.form["audienceSlider"])
    limit = int(request.form["limit"])

    print(genres) # accounted for in URL
    print(ratings) # accounted for in URL
    print(platforms) # accounted for in URL
    print(tomatometerScore) 
    print(audienceScore)
    print(limit) # ^ These three need to be filtered in scraping func

    URLs = scraper.generateURLs(
        "MOVIE", genres, ratings, platforms, tomatometerScore, audienceScore, limit
    )
    movieInfo = scraper.scrapeMovies(
        URLs, tomatometerScore, audienceScore, limit
    )

    return render_template("movieRecommendations.html", movieInfo=movieInfo)