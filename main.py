from flask import Flask, render_template, request, Response
import scraping.scraper as scraper
from rq import Queue
from rq.job import Job
import json
import time
from worker import conn
import os
import redis
from dotenv import load_dotenv

# Load environment variables and run app
load_dotenv()
app = Flask(__name__)

# Use Redis for cache
cache = conn
q = Queue(connection=conn)

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

        # Generate a cache key from the client filters
        keyArray = [
            "M", "".join(genres), "".join(ratings), "".join(platforms), "T",
            formData["tomatometerSlider"], "A", formData["audienceSlider"], "L", 
            formData["limit"]
        ]
        if popular:
            keyArray.append("P")
        key = "".join(keyArray)
        
        value = cache.get(key)
        if value is not None:
            return {'job_id': value}
        
        # Generate a list of URLs to search 
        URLs = scraper.generateMovieURLs(
            genres, ratings, platforms, tomatometerScore, audienceScore, limit, popular
        )

        # Enqueue the job
        scraper.scrapeMovies(URLs, tomatometerScore, audienceScore, limit)
        job = q.enqueue(
            scraper.scrapeMovies, URLs, tomatometerScore, audienceScore, limit, result_ttl=86400
        )
        job.meta['key'] = key
        job.save_meta()
        return {'job_id': job.id}
    except Exception as e:
        print("Error enqueuing movies job", e)
        return {}

# Get progress of current job
@app.route('/movies/progress/<string:id>', methods=['GET'])
def movieProgress(id):
    def movieStatus():
        try:
            job = Job.fetch(id, connection=conn)
            status = job.get_status(refresh=True)
            
            # If job is finished, return the link to the recommendations page
            if status == 'finished':
                data = {'progress': 100}
                json_data = json.dumps(data)
                yield f"data:{json_data}\n\n"
                data = {'result': 'recommendations/' + job.id}
                json_data = json.dumps(data)
                yield f"data:{json_data}\n\n"
                return

            # If not, use server-sent events to yield data every second
            while status != 'finished':
                status = job.get_status()
                job.refresh()

                if 'progress' in job.meta:
                    data = {'progress': job.meta['progress']}
                    json_data = json.dumps(data)
                    yield f"data:{json_data}\n\n"
                time.sleep(1)

            job.refresh()
            cache.set(job.meta['key'], job.id, ex=86399) # Each job cached for 1 day
            data = {'result': job.meta['result']}
            json_data = json.dumps(data)
            yield f"data:{json_data}\n\n"

        except Exception as e:
            print("Error getting movie job status", e)
            return {}
    return Response(movieStatus(), mimetype='text/event-stream')

# Return the recommendations page for a given job id
@app.route('/movies/recommendations/<string:id>/', methods=['GET'])
def movieRecommendations(id):   
    try: 
        job = Job.fetch(id, connection=conn)

        if job.get_status() == 'finished':
            movieInfo = job.result

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

        # Generate cache key from client filters
        keyArray = [
            "T", "".join(genres), "".join(ratings), "".join(platforms), "T",
            formData["tomatometerSlider"], "A", formData["audienceSlider"], "L", 
            formData["limit"]
        ]
        if popular:
            keyArray.append("P")
        key = "".join(keyArray)

        value = cache.get(key)
        if value is not None:
            return {'job_id': value}

        # Generate list of URLs to search based on filters
        URLs = scraper.generateTVshowURLs(
            genres, ratings, platforms, tomatometerScore, audienceScore, limit, popular
        )

        # Enqueue a job that stores its result for 1 day
        scraper.scrapeTVshows(URLs, tomatometerScore, audienceScore, limit)
        job = q.enqueue(
            scraper.scrapeTVshows, URLs, tomatometerScore, audienceScore, limit, result_ttl=86400
        )

        job.meta['key'] = key
        job.save_meta()
        return {'job_id': job.id}
    except Exception as e:
        print("Error enqueuing tv show job", e)
        return {}

# Progress for tv show scraping job
@app.route('/tvshows/progress/<string:id>', methods=['GET'])
def tvshowProgress(id):
    def tvshowStatus():
        try:
            job = Job.fetch(id, connection=conn)
            status = job.get_status()

            # If job is finished, return the recommendations page link
            if status == 'finished':
                data = {'progress': 100}
                json_data = json.dumps(data)
                yield f"data:{json_data}\n\n"
                data = {'result': 'recommendations/' + job.id}
                json_data = json.dumps(data)
                yield f"data:{json_data}\n\n"
                return

            # If job, yield progress from 0-99 every second with SSE
            while status != 'finished':
                status = job.get_status()
                job.refresh()
                
                if 'progress' in job.meta:
                    data = {'progress': job.meta['progress']}
                    json_data = json.dumps(data)
                    yield f"data:{json_data}\n\n"
                time.sleep(1)

            # When job finishes, return the recommendations page link
            job.refresh()
            cache.set(job.meta['key'], job.id, ex=86399)
            data = {'result': job.meta['result']}
            json_data = json.dumps(data)
            yield f"data:{json_data}\n\n"

        except Exception as e:
            print("Error getting tv show job status", e)
            return {}
    return Response(tvshowStatus(), mimetype='text/event-stream')

# TV show recommendations page for a given job id
@app.route('/tvshows/recommendations/<string:id>/', methods=['GET'])
def tvshowRecommendations(id):
    try: 
        job = Job.fetch(id, connection=conn)

        if job.get_status() == 'finished':
            tvshowInfo = job.result

            if len(tvshowInfo[0]) == 0:
                return render_template("tvshowNotFound.html")

            return render_template("tvshowRecommendations.html", tvShowInfo=tvshowInfo)
        return "Job in progress", 400

    except Exception as e:
        print("Error getting movies rec page", e)
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

        # Generate a cache key
        keyArray = [
            "A", actor, "".join(formData["category"]), "".join(roles), 
            formData["yearSlider"], "B", formData["boxOffice"], "".join(genres), 
            "".join(ratings), "".join(platforms), "T", formData["tomatometerSlider"],
            "A", formData["audienceSlider"], "L", formData["limit"] 
        ]
        key = "".join(keyArray)

        value = cache.get(key)
        if value is not None:
            return {'job_id': value}

        job = q.enqueue(
            scraper.scrapeActor, filterData, result_ttl=86400
        )
        job.meta["key"] = key
        job.save_meta()
        return {'job_id': job.id}
    except Exception as e:
        print("Error getting actor job", e)
        return {}

# Get progress for an actor scraping job for a given id
@app.route('/actor/progress/<string:id>', methods=['GET'])
def actorProgress(id):
    def actorStatus():
        try:
            job = Job.fetch(id, connection=conn)
            status = job.get_status()

            if status == 'finished':
                data = {'progress': 100}
                json_data = json.dumps(data)
                yield f"data:{json_data}\n\n"
                data = {'result': 'recommendations/' + job.id}
                json_data = json.dumps(data)
                yield f"data:{json_data}\n\n"
                return

            while status != 'finished':
                status = job.get_status()
                job.refresh()

                if 'progress' in job.meta:
                    data = {'progress': job.meta['progress']}
                    json_data = json.dumps(data)
                    yield f"data:{json_data}\n\n"
                time.sleep(1)

            job.refresh()
            cache.set(job.meta["key"], job.id, ex=86399)
            data = {'result': job.meta['result']}
            json_data = json.dumps(data)
            yield f"data:{json_data}\n\n"

        except Exception as e:
            print("Error getting actor job progress", e)
            return {}
    return Response(actorStatus(), mimetype='text/event-stream')

# Actor recommendations page for a given id
@app.route('/actor/recommendations/<string:id>', methods=['GET'])
def actorRecommendations(id):
    try: 
        job = Job.fetch(id, connection=conn)

        if job.get_status() == 'finished':
            actorInfo = job.result

            if actorInfo is None:
                return render_template("actorInvalid.html")
    
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
        director = formData["directorURL"].split("/")[-1]
        # Cache key
        keyArray = [
            "D", director, "".join(formData["category"]), formData["yearSlider"],
            "B", formData["boxOffice"], "".join(genres), "".join(ratings), 
            "".join(platforms), "T", formData["tomatometerSlider"], "A", 
            formData["audienceSlider"], "L", formData["limit"] 
        ]
        key = "".join(keyArray)

        value = cache.get(key)
        if value is not None:
            return {'job_id': value}

        job = q.enqueue(
            scraper.scrapeDirectorProducer, filterData, "director", result_ttl=86400
        )
        job.meta['key'] = key
        job.save_meta()
        return {"job_id": job.id}
    except Exception as e:
        print("Error enqueuing director job", e)
        return {}

# For a given id, get progress of director scraping job
@app.route('/director/progress/<string:id>', methods=['GET'])
def directorProgress(id):
    def directorStatus():
        try:
            job = Job.fetch(id, connection=conn)
            status = job.get_status()

            if status == 'finished':
                data = {'progress': 100}
                json_data = json.dumps(data)
                yield f"data:{json_data}\n\n"
                data = {'result': 'recommendations/' + job.id}
                json_data = json.dumps(data)
                yield f"data:{json_data}\n\n"
                return

            while status != 'finished':
                status = job.get_status()
                job.refresh()

                if 'progress' in job.meta:
                    data = {'progress': job.meta['progress']}
                    json_data = json.dumps(data)
                    yield f"data:{json_data}\n\n"
                time.sleep(1)

            job.refresh()
            cache.set(job.meta['key'], job.id, ex=86399)
            data = {'result': job.meta['result']}
            json_data = json.dumps(data)
            yield f"data:{json_data}\n\n"

        except Exception as e:
            print("Error getting progress of director job", e)
            return {}
    return Response(directorStatus(), mimetype='text/event-stream')

# Director recommendations page for a given id
@app.route('/director/recommendations/<string:id>', methods=['GET'])
def directorRecommendations(id):
    try: 
        job = Job.fetch(id, connection=conn)

        if job.get_status() == 'finished':
            directorInfo = job.result

            if directorInfo is None:
                return render_template("directorInvalid.html")
    
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
        producer = formData["producerURL"].split("/")[-1]
        # Cache key based on filter data
        keyArray = [
            "P", producer, "".join(formData["category"]), formData["yearSlider"],
            "B", formData["boxOffice"], "".join(genres), "".join(ratings), 
            "".join(platforms), "T", formData["tomatometerSlider"], "A", 
            formData["audienceSlider"], "L", formData["limit"] 
        ]
        key = "".join(keyArray)
        value = cache.get(key)
        if value is not None:
            return {'job_id': value}

        # Enqueue the job if the results aren't cached
        job = q.enqueue(
            scraper.scrapeDirectorProducer, filterData, "producer", result_ttl=86400
        )
        job.meta['key'] = key
        job.save_meta()
        return {"job_id": job.id}
    except Exception as e:
        print("Error enqueuing producer job", e)
        return {}

# Given an id, return the progress of a producer scraping job
@app.route('/producer/progress/<string:id>', methods=['GET'])
def producerProgress(id):
    def producerStatus():
        try:
            job = Job.fetch(id, connection=conn)
            status = job.get_status()

            if status == 'finished':
                data = {'progress': 100}
                json_data = json.dumps(data)
                yield f"data:{json_data}\n\n"
                data = {'result': 'recommendations/' + job.id}
                json_data = json.dumps(data)
                yield f"data:{json_data}\n\n"
                return

            while status != 'finished':
                status = job.get_status()
                job.refresh()

                if 'progress' in job.meta:
                    data = {'progress': job.meta['progress']}
                    json_data = json.dumps(data)
                    yield f"data:{json_data}\n\n"
                time.sleep(1)

            job.refresh()
            cache.set(job.meta['key'], job.id, ex=86399)
            data = {'result': job.meta['result']}
            json_data = json.dumps(data)
            yield f"data:{json_data}\n\n"

        except Exception as e:
            print("Error getting producer job status", e)
            return {}
    return Response(producerStatus(), mimetype='text/event-stream')

# Producer recommendations page for a given id
@app.route('/producer/recommendations/<string:id>', methods=['GET'])
def producerRecommendations(id):
    try: 
        job = Job.fetch(id, connection=conn)

        if job.get_status() == 'finished': 
            producerInfo = job.result

            if producerInfo is None:
                return render_template("producerInvalid.html")
    
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
        # Cache key
        key = "".join(keyArray)
        value = cache.get(key)
        if value is not None:
            return {'job_id': value}

        job = q.enqueue(
            scraper.scrapeSimilar, filterData, result_ttl=86400
        )
        job.meta["key"] = key
        job.save_meta()
        return {'job_id': job.id}
    except Exception as e:
        print("Error enqueuing similar job", e)
        return {}

# Given an id, get the progress of a similar scraping job
@app.route('/similar/progress/<string:id>', methods=['GET'])
def similarProgress(id):
    def similarStatus():
        try:
            job = Job.fetch(id, connection=conn)
            status = job.get_status()

            if status == 'finished':
                data = {'progress': 100}
                json_data = json.dumps(data)
                yield f"data:{json_data}\n\n"
                data = {'result': 'recommendations/' + job.id}
                json_data = json.dumps(data)
                yield f"data:{json_data}\n\n"
                return

            while status != 'finished':
                status = job.get_status()
                job.refresh()

                if 'progress' in job.meta:
                    data = {'progress': job.meta['progress']}
                    json_data = json.dumps(data)
                    yield f"data:{json_data}\n\n"
                time.sleep(1)

            job.refresh()
            cache.set(job.meta["key"], job.id, ex=86399)
            data = {'result': job.meta['result']}
            json_data = json.dumps(data)
            yield f"data:{json_data}\n\n"

        except Exception as e:
            print("Error getting progress of similar job", e)
            return {}
    return Response(similarStatus(), mimetype='text/event-stream')

# Similar recommendations page for a job id
@app.route('/similar/recommendations/<string:id>', methods=['GET'])
def similarRecommendations(id):
    try: 
        job = Job.fetch(id, connection=conn)

        if job.get_status() == 'finished': 
            similarInfo = job.result

            if similarInfo is None:
                return render_template("similarInvalid.html")
    
            if len(similarInfo[0]) == 0:
                return render_template("similarNotFound.html")
            
            if similarInfo[0][0]["similar"] == "movie":
                return render_template(
                    "similarMovieRecommendations.html", movieInfo=similarInfo
                )
            
            if similarInfo[0][0]["similar"] == "tv":
                return render_template(
                    "similarTVRecommendations.html", tvShowInfo=similarInfo
                )

            return render_template(
                "similarRecommendations.html", similarInfo=similarInfo
            )
        return "Job in progress", 400

    except Exception as e:
        print("Error getting progress of similar job", e)
        return "Record not found", 400
