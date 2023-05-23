from flask import render_template, request, Response
import scraping.scraper as scraper
import json
import time
import os
import redis
from celery.result import AsyncResult
import hashlib
from app import app, celery_app

# Use Redis for cache
if os.getenv('APP_MODE') == 'production':
    conn = redis.from_url(os.getenv('REDIS_URL', ''))
else:
    conn = redis.from_url('redis://localhost:6379')
cache = conn

# Helper func that generates json SSE for a given job
def jobStatus(id):
    try:
        job = AsyncResult(id, app=celery_app)

        # While job is running, use server-sent events to yield data every second
        while not job.ready():
            if job.info and 'progress' in job.info:
                data = {'progress': job.info['progress']}
                json_data = json.dumps(data)
                yield f"data:{json_data}\n\n"
            time.sleep(1)

        # If job failed, return error
        if job.failed():
            data = {'failure': True}
            json_data = json.dumps(data)
            yield f"data:{json_data}\n\n"
            job.forget()
            return
        
        # If job is finished, return the link to the recommendations page
        data = {'progress': 100}
        json_data = json.dumps(data)
        yield f"data:{json_data}\n\n"
        if job.info and 'result' in job.info:
            data = {'result': job.info['result']}
            json_data = json.dumps(data)
            yield f"data:{json_data}\n\n"
            cache.set(job.info['key'], job.id, ex=86399) # Each job cached for 1 day
            return
        else:
            data = {'failure': True}
            json_data = json.dumps(data)
            yield f"data:{json_data}\n\n"
            job.forget()
            return

    except Exception as e:
        print("Error getting job status", e)
        data = {'failure': True}
        json_data = json.dumps(data)
        yield f"data:{json_data}\n\n"
        job.forget()
        return

@app.route('/')
def index():
    return render_template("index.html")

# Movies form page
@app.route('/movies/', methods=['GET'])
def movies():
    return render_template('movies.html')

# Enqueue movie scraping job in worker queue
@app.route('/movies/enqueue/', methods=['POST'])
def moviesEnqueue():
    try:
        formData = request.form
        genres = formData.getlist("genres")
        ratings = formData.getlist("ratings")
        platforms = formData.getlist("platforms")
        tomatometerScore = int(formData["tomatometerSlider"])
        audienceScore = int(formData["audienceSlider"])
        limit = 10 if formData["limit"] == "" else int(formData["limit"])
        popular = True if "popular" in formData else False

        # Generate a cache key and return cache hit
        keyArray = [
            "M", "".join(genres), "".join(ratings), "".join(platforms), "T",
            formData["tomatometerSlider"], "A", formData["audienceSlider"], "L", 
            formData["limit"]
        ]
        if popular:
            keyArray.append("P")
        key = "".join(keyArray)
        keyHash = hashlib.sha1(key.encode()).hexdigest()
        value = cache.get(keyHash)
        if value is not None:
            return {'job_id': value.decode()}
        
        # Generate a list of URLs to search 
        URLs = scraper.generateMovieURLs(
            genres, ratings, platforms, tomatometerScore, audienceScore, limit, popular
        )
        # Enqueue the job on a cache miss
        job = scraper.scrapeMovies.delay(URLs, tomatometerScore, audienceScore, limit, key=keyHash)
        return {'job_id': job.id}
    except Exception as e:
        print("Error enqueuing movies job", e)
        return {} # Need better handling here, but this shouldn't ever throw an error

# Get progress of current job
@app.route('/movies/progress/<string:id>', methods=['GET'])
def movieProgress(id):
    return Response(jobStatus(id), mimetype='text/event-stream')

# Return the recommendations page for a given job id
@app.route('/movies/recommendations/<string:id>/', methods=['GET'])
def movieRecommendations(id):   
    try: 
        job = AsyncResult(id, app=celery_app)
        if job.ready():
            if job.failed():
                return render_template("movieError.html")
            # You'd want to check for error and redirect to another page here
            movieInfo = job.result["movieInfo"]

            # No recommendations found
            if len(movieInfo[0]) == 0:
                return render_template("movieNotFound.html")
            return render_template("movieRecommendations.html", movieInfo=movieInfo)
        return "Job in progress", 400

    # If job id not in Redis, it expired
    except Exception as e:
        print("Error getting movie rec page", e)
        return "Record not found", 400

# TV shows form page
@app.route('/tvshows/', methods=['GET'])
def tvshows():
    return render_template('tvshows.html')

# Enqueue tv show scraping in worker queue
@app.route('/tvshows/enqueue/', methods=['POST'])
def tvshowsEnqueue():
    try:
        formData = request.form
        genres = formData.getlist("genres")
        ratings = formData.getlist("ratings")
        platforms = formData.getlist("platforms")
        tomatometerScore = int(formData["tomatometerSlider"])
        audienceScore = int(formData["audienceSlider"])
        limit = 10 if formData["limit"] == "" else int(formData["limit"])
        popular = True if "popular" in formData else False

        # Generate cache key, return cache hit
        keyArray = [
            "T", "".join(genres), "".join(ratings), "".join(platforms), "T",
            formData["tomatometerSlider"], "A", formData["audienceSlider"], "L", 
            formData["limit"]
        ]
        if popular:
            keyArray.append("P")
        key = "".join(keyArray)
        keyHash = hashlib.sha1(key.encode()).hexdigest()
        value = cache.get(keyHash)
        if value is not None:
            return {'job_id': value.decode()}

        # Generate list of URLs to search based on filters
        URLs = scraper.generateTVshowURLs(
            genres, ratings, platforms, tomatometerScore, audienceScore, limit, popular
        )
        # Enqueue the job on a cache miss
        job = scraper.scrapeTVshows.delay(URLs, tomatometerScore, audienceScore, limit, key=keyHash)
        return {'job_id': job.id}
    except Exception as e:
        print("Error enqueuing tv show job", e)
        return {}

# Progress for tv show scraping job
@app.route('/tvshows/progress/<string:id>', methods=['GET'])
def tvshowProgress(id):
    return Response(jobStatus(id), mimetype='text/event-stream')

# TV show recommendations page for a given job id
@app.route('/tvshows/recommendations/<string:id>/', methods=['GET'])
def tvshowRecommendations(id):
    try: 
        job = AsyncResult(id, app=celery_app)
        if job.ready():
            if job.failed():
                return render_template("tvshowError.html")
            tvShowInfo = job.result["tvShowInfo"]

            # No recommendations found
            if len(tvShowInfo[0]) == 0:
                return render_template("tvshowNotFound.html")
            return render_template("tvshowRecommendations.html", tvShowInfo=tvShowInfo)
        return "Job in progress", 400

    except Exception as e:
        print("Error getting tv show rec page", e)
        return "Record not found", 400

# Movies/tv shows by actor form page
@app.route('/actor/', methods=['GET'])
def actor():
    return render_template('actor.html')

# Enqueue a scraping job for actor movies/tv shows
@app.route('/actor/enqueue/', methods=['POST'])
def actorEnqueue():
    try:
        formData = request.form
        roles = formData.getlist("role")
        if len(roles) == 0 or "all" in roles:
            roles = ["all"]
        genres = formData.getlist("genres")
        if len(genres) == 0 or "all" in genres:
            genres = ["all"]
        ratings = formData.getlist("ratings")
        if len(ratings) == 0 or "all" in ratings:
            ratings = ["all"]
        platforms = formData.getlist("platforms")
        if len(platforms) == 0 or "all" in platforms:
            platforms = ["all"]

        filterData = {
            "actorURL": formData["actorURL"],
            "category": formData["category"],
            "roles": roles,
            "oldestYear": int(formData["yearSlider"]),
            "boxOffice": int(formData["boxOffice"]),
            "genres": genres,
            "ratings": ratings,
            "platforms": platforms,
            "tomatometerScore": int(formData["tomatometerSlider"]),
            "audienceScore": int(formData["audienceSlider"]),
            "limit": 10 if formData["limit"] == "" else int(formData["limit"])
        }
        actor = formData["actorURL"].split("/")[-1]

        # Generate a cache key and return a cache hit
        keyArray = [
            "A", actor, "".join(formData["category"]), "".join(roles), 
            formData["yearSlider"], "B", formData["boxOffice"], "".join(genres), 
            "".join(ratings), "".join(platforms), "T", formData["tomatometerSlider"],
            "A", formData["audienceSlider"], "L", formData["limit"] 
        ]
        key = "".join(keyArray)
        keyHash = hashlib.sha1(key.encode()).hexdigest()
        value = cache.get(keyHash)
        if value is not None:
            return {'job_id': value.decode()}

        # Enqueue the job on a cache miss
        job = scraper.scrapeActor.delay(filterData, key=keyHash)
        return {'job_id': job.id}
    except Exception as e:
        print("Error getting actor job", e)
        return {}

# Get progress for an actor scraping job for a given id
@app.route('/actor/progress/<string:id>', methods=['GET'])
def actorProgress(id):
    return Response(jobStatus(id), mimetype='text/event-stream')

# Actor recommendations page for a given id
@app.route('/actor/recommendations/<string:id>', methods=['GET'])
def actorRecommendations(id):
    try: 
        job = AsyncResult(id, app=celery_app)
        if job.ready():
            if job.failed():
                return render_template("actorError.html")
            actorInfo = job.result["actorInfo"]
            # Invalid actor url
            if actorInfo is None:
                return render_template("actorInvalid.html")
            # No recommendations found
            if len(actorInfo[0]) == 0:
                return render_template("actorNotFound.html")
            return render_template("actorRecommendations.html", actorInfo=actorInfo)
        return "Job in progress", 400

    except Exception as e:
        print("Error getting actor rec page", e)
        return "Record not found", 400

# Movies/tv shows by director form page
@app.route('/director/', methods=['GET'])
def director():
    return render_template('director.html')

# Enqueue a director scraping job
@app.route('/director/enqueue/', methods=['POST'])
def directorEnqueue():
    try:
        formData = request.form
        genres = formData.getlist("genres")
        if len(genres) == 0 or "all" in genres:
            genres = ["all"]
        ratings = formData.getlist("ratings")
        if len(ratings) == 0 or "all" in ratings:
            ratings = ["all"]
        platforms = formData.getlist("platforms")
        if len(platforms) == 0 or "all" in platforms:
            platforms = ["all"]
        filterData = {
            "url": formData["directorURL"],
            "category": formData["category"],
            "oldestYear": int(formData["yearSlider"]),
            "boxOffice": int(formData["boxOffice"]),
            "genres": genres,
            "ratings": ratings,
            "platforms": platforms,
            "tomatometerScore": int(formData["tomatometerSlider"]),
            "audienceScore": int(formData["audienceSlider"]),
            "limit": 10 if formData["limit"] == "" else int(formData["limit"])
        }
        # Generate a cache key and return cache hit
        director = formData["directorURL"].split("/")[-1]
        keyArray = [
            "D", director, "".join(formData["category"]), formData["yearSlider"],
            "B", formData["boxOffice"], "".join(genres), "".join(ratings), 
            "".join(platforms), "T", formData["tomatometerSlider"], "A", 
            formData["audienceSlider"], "L", formData["limit"] 
        ]
        key = "".join(keyArray)
        keyHash = hashlib.sha1(key.encode()).hexdigest()
        value = cache.get(keyHash)
        if value is not None:
            return {'job_id': value.decode()}
        
        # Enqueue the job on a cache miss
        job = scraper.scrapeDirectorProducer.delay(filterData, "director", key=keyHash)
        return {"job_id": job.id}
    except Exception as e:
        print("Error enqueuing director job", e)
        return {}

# For a given id, get progress of director scraping job
@app.route('/director/progress/<string:id>', methods=['GET'])
def directorProgress(id):
    return Response(jobStatus(id), mimetype='text/event-stream')

# Director recommendations page for a given id
@app.route('/director/recommendations/<string:id>', methods=['GET'])
def directorRecommendations(id):
    try: 
        job = AsyncResult(id, app=celery_app)
        if job.ready():
            if job.failed():
                return render_template("directorError.html")
            directorInfo = job.result['filmographyInfo']
            # Invalid director url
            if directorInfo is None:
                return render_template("directorInvalid.html")
            # No recommendations found
            if len(directorInfo[0]) == 0:
                return render_template("directorNotFound.html")
            return render_template("directorRecommendations.html", directorInfo=directorInfo)
        return "Job in progress", 400

    except Exception as e:
        print("Error getting director rec page", e)
        return "Record not found", 400

# Movies/tv shows by producer page
@app.route('/producer/', methods=['GET'])
def producer():
    return render_template('producer.html')

# Enqueue a producer scraping job
@app.route('/producer/enqueue/', methods=['POST'])
def producerEnqueue():
    try:
        formData = request.form
        genres = formData.getlist("genres")
        if len(genres) == 0 or "all" in genres:
            genres = ["all"]
        ratings = formData.getlist("ratings")
        if len(ratings) == 0 or "all" in ratings:
            ratings = ["all"]
        platforms = formData.getlist("platforms")
        if len(platforms) == 0 or "all" in platforms:
            platforms = ["all"]
        filterData = {
            "url": formData["producerURL"],
            "category": formData["category"],
            "oldestYear": int(formData["yearSlider"]),
            "boxOffice": int(formData["boxOffice"]),
            "genres": genres,
            "ratings": ratings,
            "platforms": platforms,
            "tomatometerScore": int(formData["tomatometerSlider"]),
            "audienceScore": int(formData["audienceSlider"]),
            "limit": 10 if formData["limit"] == "" else int(formData["limit"])
        }

        # Generate a cache key and return cache hit
        producer = formData["producerURL"].split("/")[-1]
        keyArray = [
            "P", producer, "".join(formData["category"]), formData["yearSlider"],
            "B", formData["boxOffice"], "".join(genres), "".join(ratings), 
            "".join(platforms), "T", formData["tomatometerSlider"], "A", 
            formData["audienceSlider"], "L", formData["limit"] 
        ]
        key = "".join(keyArray)
        keyHash = hashlib.sha1(key.encode()).hexdigest()
        value = cache.get(keyHash)
        if value is not None:
            return {'job_id': value.decode()}

        # Enqueue the job on a cache miss
        job = scraper.scrapeDirectorProducer.delay(filterData, "producer", key=keyHash)
        return {"job_id": job.id}
    except Exception as e:
        print("Error enqueuing producer job", e)
        return {}

# Given an id, return the progress of a producer scraping job
@app.route('/producer/progress/<string:id>', methods=['GET'])
def producerProgress(id):
    return Response(jobStatus(id), mimetype='text/event-stream')

# Producer recommendations page for a given id
@app.route('/producer/recommendations/<string:id>', methods=['GET'])
def producerRecommendations(id):
    try: 
        job = AsyncResult(id, app=celery_app)
        if job.ready():
            if job.failed():
                return render_template("producerError.html")
            producerInfo = job.result["filmographyInfo"]
            # Invalid producer URL
            if producerInfo is None:
                return render_template("producerInvalid.html")
            # No recommendations found
            if len(producerInfo[0]) == 0:
                return render_template("producerNotFound.html")
            return render_template("producerRecommendations.html", producerInfo=producerInfo)
        return "Job in progress", 400

    except Exception as e:
        print("Error getting producer rec page", e)
        return "Record not found", 400

# Form page for similar movies/shows
@app.route('/similar/', methods=['GET'])
def similar():
    return render_template('similar.html')

# Enqueue a similar scraping job
@app.route('/similar/enqueue/', methods=['POST'])
def similarEnqueue():
    try:
        formData = request.form
        platforms = formData.getlist("platforms")
        if len(platforms) == 0 or "all" in platforms:
            platforms = ["all"]
        filterData = {
            "url": formData["url"],
            "oldestYear": int(formData["yearSlider"]),
            "platforms": platforms,
            "tomatometerScore": int(formData["tomatometerSlider"]),
            "audienceScore": int(formData["audienceSlider"]),
            "limit": 10 if formData["limit"] == "" else int(formData["limit"])
        }
        media = formData["url"].split("/")[-1]
        keyArray = [
            "S", media, formData["yearSlider"], "".join(platforms), "T",
            formData["tomatometerSlider"], "A", formData["audienceSlider"], 
            "L", formData["limit"]
        ]
        # Generate a cache key and return cache hit
        key = "".join(keyArray)
        keyHash = hashlib.sha1(key.encode()).hexdigest()
        value = cache.get(keyHash)
        if value is not None:
            return {'job_id': value.decode()}

        job = scraper.scrapeSimilar.delay(filterData, key=keyHash)
        return {'job_id': job.id}
    except Exception as e:
        print("Error enqueuing similar job", e)
        return {}

# Given an id, get the progress of a similar scraping job
@app.route('/similar/progress/<string:id>', methods=['GET'])
def similarProgress(id):
    return Response(jobStatus(id), mimetype='text/event-stream')

# Similar recommendations page for a job id
@app.route('/similar/recommendations/<string:id>', methods=['GET'])
def similarRecommendations(id):
    try: 
        job = AsyncResult(id, app=celery_app)
        if job.ready():
            if job.failed():
                return render_template("similarError.html")
            similarInfo = job.result["similarInfo"]
            # Bad similar media URL
            if similarInfo is None:
                return render_template("similarInvalid.html")
            # No recommendations found
            if len(similarInfo[0]) == 0:
                return render_template("similarNotFound.html")
            # Return page based on media type
            if similarInfo[0][0]["type"] == "movie":
                return render_template(
                    "similarMovieRecommendations.html", movieInfo=similarInfo
                )
            if similarInfo[0][0]["type"] == "tv":
                return render_template(
                    "similarTVRecommendations.html", tvShowInfo=similarInfo
                )
            # Vestigial, but will keep for now
            return render_template(
                "similarRecommendations.html", similarInfo=similarInfo
            )
        return "Job in progress", 400

    except Exception as e:
        print("Error getting progress of similar job", e)
        return "Record not found", 400
