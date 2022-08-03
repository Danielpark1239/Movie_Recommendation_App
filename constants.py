# Number of entries that Rotten Tomatoes shows per page
ENTRIES_PER_PAGE = 30
MAX_LIMIT = 50

# If scores are above a certain threshold, generate more pages to search
GOURMET_THRESHOLD = 75
FRESH_THRESHOLD = 60
RANDOM_THRESHOLD = 75

BASE_URL = "https://www.rottentomatoes.com"
BASE_MOVIE_THEATERS_URL = "https://www.rottentomatoes.com/browse/movies_in_theaters/"
BASE_MOVIE_HOME_URL = "https://www.rottentomatoes.com/browse/movies_at_home/"
BASE_TV_URL = "https://www.rottentomatoes.com/browse/tv_series_browse/"

# Mapping from platform to correct URL representation
URL_PLATFORM_DICT = {
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

# Mapping from platform to frontend representation
FRONTEND_PLATFORM_DICT = {
    "showtimes": "In Theaters",
    "amazon-prime-video-us": "Amazon Prime Video",
    "itunes": "iTunes",
    "apple-tv-plus-us": "Apple TV+",
    "disney-plus-us": "Disney+",
    "hbo-max": "HBO Max",
    "hulu": "Hulu",
    "netflix": "Netflix",
    "paramount-plus-us": "Paramount+",
    "peacock": "Peacock",
    "vudu": "Vudu"
}

# Relative path works in templates folder
BLANK_POSTER = "../../static/blank_poster.png"

