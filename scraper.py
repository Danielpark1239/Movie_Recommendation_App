def generateURLs(type, genres, ratings, platforms):
    URLs = []
    if type == "MOVIE":
        theatersURL = "https://www.rottentomatoes.com/browse/movies_in_theaters/"
        homeURL = "https://www.rottentomatoes.com/browse/movies_at_home/"

        if "all" in genres or len(genres) == 0:
            genreString = ""
        else:
            genreString = "genres:" + ",".join(genres) + "~"
        
        if "all" in ratings or len(ratings) == 0:
            ratingString = ""
        else:
            ratingString = "ratings:" + ",".join(ratings) + "~"

        if len(platforms) == 0:
            platforms.append("all")

        # Generate from theatersURL
        if "all" in platforms or "showtimes" in platforms:
            if "showtimes" in platforms:
                platforms.remove("showtimes")
            URLs.append(theatersURL + genreString + ratingString + "sort:popular?page=1")
        
        # Generate from homeURL
        if "all" in platforms or len(platforms) > 0:
            if "all" in platforms:
                platformString = ""

            else:
                # Mapping from platform to correct URL representation
                platformDict = {
                    "amazon-prime-video-us": "amazon_prime",
                    "itunes": "apple_tv",
                    "apple-tv-plus-us": "apple_tv_plus",
                    "disney-plus-us": "disney_plus",
                    "hbo-max": "hbo_max",
                    "hulu": "hulu",
                    "netflix": "netflix",
                    "paramount-plus-us": "paramount_plus",
                    "peacock": "peacock",
                    "vudu": "vudu"
                }
                platforms = [platformDict[platform] for platform in platforms]
                platformString = "affiliates:" + ",".join(platforms) + "~"

            URLs.append(homeURL + platformString + genreString + ratingString + "sort:popular?page=1")

        return URLs