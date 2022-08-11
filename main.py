from base64 import decode
from flask import render_template, request, Response
import scraper
from rq import Queue
from rq.job import Job
from app import app
import json
import time
from worker import conn
import os
import redis

redis_url = os.getenv('HEROKU_REDIS_OLIVE_URL', 'redis://localhost:6379')
redis = redis.from_url(redis_url, decode_responses=True)
q = Queue(connection=conn)

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/movies/', methods=['GET'])
def movies():
    return render_template('movies.html')

@app.route('/movies/enqueue/', methods=['POST'])
def moviesEnqueue():
    formData = request.form
    genres = formData.getlist("genres")
    ratings = formData.getlist("ratings")
    platforms = formData.getlist("platforms")
    tomatometerScore = int(formData["tomatometerSlider"])
    audienceScore = int(formData["audienceSlider"])
    limit = 10 if formData["limit"] == "" else int(formData["limit"])
    popular = True if "popular" in formData else False

    keyArray = [
        "M", "".join(genres), "".join(ratings), "".join(platforms),
        formData["tomatometerSlider"], formData["audienceSlider"], formData["limit"]]
    if popular:
        keyArray.append("P")
    key = "".join(keyArray)

    value = redis.get(key)
    if value is not None:
        return {'job_id': value}
    
    URLs = scraper.generateMovieURLs(
        genres, ratings, platforms, tomatometerScore, audienceScore, limit, popular
    )
    job = q.enqueue(
        scraper.scrapeMovies, URLs, tomatometerScore, audienceScore, limit, result_ttl=86400
    )
    job.meta['key'] = key
    job.save_meta()
    return {'job_id': job.id}

@app.route('/movies/progress/<string:id>', methods=['GET'])
def movieProgress(id):
    def movieStatus():
        try:
            job = Job.fetch(id, connection=conn)
            status = job.get_status(refresh=True)
            print(status)
            
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
                else:
                    data = {'progress': job.meta['progress']}

                json_data = json.dumps(data)
                yield f"data:{json_data}\n\n"
                time.sleep(1)

            job.refresh()
            redis.set(job.meta['key'], job.id, ex=86399)
            data = {'result': job.meta['result']}
            json_data = json.dumps(data)
            yield f"data:{json_data}\n\n"

        except:
            return {}
    return Response(movieStatus(), mimetype='text/event-stream')

@app.route('/movies/recommendations/<string:id>/', methods=['GET'])
def movieRecommendations(id):
    # TO-DO: What if job expires?
        # Possible solutions:
        # 1. Lazy: Just throw an error or URL not found
        # 2. Store result in a database and pull from it, but what if that data gets rolled over and can't be found?
        # 3. Most involved: learn a framework and do client-side rendering
    
    try: 
        job = Job.fetch(id, connection=conn)

        if job.get_status() == 'finished':
            movieInfo = job.result

            if len(movieInfo[0]) == 0:
                return render_template("movieNotFound.html")

            return render_template("movieRecommendations.html", movieInfo=movieInfo)

    except:
        return "Record not found", 400

@app.route('/tvshows/', methods=['GET'])
def tvshows():
    return render_template('tvshows.html')

@app.route('/tvshows/enqueue/', methods=['POST'])
def tvshowsEnqueue():
    formData = request.form
    genres = formData.getlist("genres")
    ratings = formData.getlist("ratings")
    platforms = formData.getlist("platforms")
    tomatometerScore = int(formData["tomatometerSlider"])
    audienceScore = int(formData["audienceSlider"])
    limit = 10 if formData["limit"] == "" else int(formData["limit"])
    popular = True if "popular" in formData else False

    URLs = scraper.generateTVshowURLs(
        genres, ratings, platforms, tomatometerScore, audienceScore, limit, popular
    )
    job = q.enqueue(
        scraper.scrapeTVshows, URLs, tomatometerScore, audienceScore, limit, result_ttl=86400
    )

    return {'job_id': job.id}

@app.route('/tvshows/progress/<string:id>', methods=['GET'])
def tvshowProgress(id):
    def tvshowStatus():
        try:
            job = Job.fetch(id, connection=conn)
            status = job.get_status()

            while status != 'finished':
                status = job.get_status()
                job.refresh()

                if 'progress' in job.meta:
                    data = {'progress': job.meta['progress']}
                else:
                    data = {'progress': job.meta['progress']}

                json_data = json.dumps(data)
                yield f"data:{json_data}\n\n"
                time.sleep(1)

            job.refresh()
            data = {'result': job.meta['result']}
            json_data = json.dumps(data)
            yield f"data:{json_data}\n\n"

        except:
            return {}
    return Response(tvshowStatus(), mimetype='text/event-stream')

@app.route('/tvshows/recommendations/<string:id>/', methods=['GET'])
def tvshowRecommendations(id):
    try: 
        job = Job.fetch(id, connection=conn)

        if job.get_status() == 'finished':
            tvshowInfo = job.result

            if len(tvshowInfo[0]) == 0:
                return render_template("tvshowNotFound.html")

        return render_template("tvshowRecommendations.html", tvShowInfo=tvshowInfo)

    except:
        return "Record not found", 400

@app.route('/actor/', methods=['GET'])
def actor():
    return render_template('actor.html')

@app.route('/actor/enqueue/', methods=['POST'])
def actorEnqueue():
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

    job = q.enqueue(
        scraper.scrapeActor, filterData, result_ttl=86400
    )

    return {'job_id': job.id}

@app.route('/actor/progress/<string:id>', methods=['GET'])
def actorProgress(id):
    def actorStatus():
        try:
            job = Job.fetch(id, connection=conn)
            status = job.get_status()

            while status != 'finished':
                status = job.get_status()
                job.refresh()

                if 'progress' in job.meta:
                    data = {'progress': job.meta['progress']}
                else:
                    data = {'progress': job.meta['progress']}

                json_data = json.dumps(data)
                yield f"data:{json_data}\n\n"
                time.sleep(1)

            job.refresh()
            data = {'result': job.meta['result']}
            json_data = json.dumps(data)
            yield f"data:{json_data}\n\n"

        except:
            return {}
    return Response(actorStatus(), mimetype='text/event-stream')

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

    except:
        return "Record not found", 400

@app.route('/director/', methods=['GET'])
def director():
    return render_template('director.html')

@app.route('/director/enqueue/', methods=['POST'])
def directorEnqueue():
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

    job = q.enqueue(
        scraper.scrapeDirectorProducer, filterData, "director", result_ttl=86400
    )

    return {"job_id": job.id}

@app.route('/director/progress/<string:id>', methods=['GET'])
def directorProgress(id):
    def directorStatus():
        try:
            job = Job.fetch(id, connection=conn)
            status = job.get_status()

            while status != 'finished':
                status = job.get_status()
                job.refresh()

                if 'progress' in job.meta:
                    data = {'progress': job.meta['progress']}
                else:
                    data = {'progress': job.meta['progress']}

                json_data = json.dumps(data)
                yield f"data:{json_data}\n\n"
                time.sleep(1)

            job.refresh()
            data = {'result': job.meta['result']}
            json_data = json.dumps(data)
            yield f"data:{json_data}\n\n"

        except:
            return {}
    return Response(directorStatus(), mimetype='text/event-stream')

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

    except:
        return "Record not found", 400

@app.route('/producer/', methods=['GET'])
def producer():
    return render_template('producer.html')

@app.route('/producer/enqueue/', methods=['POST'])
def producerEnqueue():
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

    job = q.enqueue(
        scraper.scrapeDirectorProducer, filterData, "producer", result_ttl=86400
    )

    return {"job_id": job.id}

@app.route('/producer/progress/<string:id>', methods=['GET'])
def producerProgress(id):
    def producerStatus():
        try:
            job = Job.fetch(id, connection=conn)
            status = job.get_status()

            while status != 'finished':
                status = job.get_status()
                job.refresh()

                if 'progress' in job.meta:
                    data = {'progress': job.meta['progress']}
                else:
                    data = {'progress': job.meta['progress']}

                json_data = json.dumps(data)
                yield f"data:{json_data}\n\n"
                time.sleep(1)

            job.refresh()
            data = {'result': job.meta['result']}
            json_data = json.dumps(data)
            yield f"data:{json_data}\n\n"

        except:
            return {}
    return Response(producerStatus(), mimetype='text/event-stream')

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

    except:
        return "Record not found", 400
    
@app.route('/similar/', methods=['GET'])
def similar():
    return render_template('similar.html')

@app.route('/similar/enqueue/', methods=['POST'])
def similarEnqueue():
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

    job = q.enqueue(
        scraper.scrapeSimilar, filterData, result_ttl=86400
    )

    return {'job_id': job.id}

@app.route('/similar/progress/<string:id>', methods=['GET'])
def similarProgress(id):
    def similarStatus():
        try:
            job = Job.fetch(id, connection=conn)
            status = job.get_status()

            while status != 'finished':
                status = job.get_status()
                job.refresh()

                if 'progress' in job.meta:
                    data = {'progress': job.meta['progress']}
                else:
                    data = {'progress': job.meta['progress']}

                json_data = json.dumps(data)
                yield f"data:{json_data}\n\n"
                time.sleep(1)

            job.refresh()
            data = {'result': job.meta['result']}
            json_data = json.dumps(data)
            yield f"data:{json_data}\n\n"

        except:
            return {}
    return Response(similarStatus(), mimetype='text/event-stream')

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

    except:
        return "Record not found", 400
    

