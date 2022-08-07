# Number of entries that Rotten Tomatoes shows per page
ENTRIES_PER_PAGE = 30
MAX_LIMIT = 50

# If scores are above a certain threshold, generate more pages to search
GOURMET_THRESHOLD = 75
FRESH_THRESHOLD = 60
RANDOM_THRESHOLD = 75

APP_BASE_URL = "https://www.rt-recommendations.herokuapp.com/"
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

# Mapping of genres from movie representation to tv show representation
MOVIE_TO_TV_GENRE_DICT = {
    "all": "all",
    "Action": "Action",
    "Adventure": "Adventure",
    "Animation": "Animation",
    "Anime": "Anime",
    "Biography": "Biography",
    "Comedy": "Comedy",
    "Crime": "Crime",
    "Documentary": "Documentary",
    "Drama": "Drama",
    "Faith&spirituality": "Faith spirituality",
    "Fantasy": "Fantasy",
    "Foreign": "Foreign",
    "Game show": "Game show",
    "Health&wellness": "Health wellness",
    "History": "History",
    "Horror": "Horror",
    "House&garden": "House garden",
    "Independent": "Independent",
    "Kids&family": "Kids family",
    "Lgbtq+": "Lgbtq",
    "Music": "Music",
    "Musical": "Musical",
    "Mystery&thriller": "Mystery thriller",
    "Nature": "Nature",
    "News": "News",
    "Other": "Other",
    "Reality": "Reality",
    "Romance": "Romance",
    "Sci-Fi": "Sci fi",
    "Short": "Short",
    "Soap": "Soap",
    "Special Interest": "Special interest",
    "Sports&fitness": "Sports",
    "Stand Up": "Stand up",
    "Talk show": "Talk show",
    "Travel": "Travel",
    "Variety": "Variety",
    "War": "War",
    "Western": "Western"
}

# Mapping of genres from tv show representation to frontend representation
TV_TO_FRONTEND_GENRE_DICT = {
    "Action": "Action",
    "Adventure": "Adventure",
    "Animation": "Animation",
    "Anime": "Anime",
    "Biography": "Biography",
    "Comedy": "Comedy",
    "Crime": "Crime",
    "Documentary": "Documentary",
    "Drama": "Drama",
    "Faith spirituality": "Faith & Spirituality",
    "Fantasy": "Fantasy",
    "Foreign": "Foreign",
    "Game show": "Game Show",
    "Health wellness": "Health & Wellness",
    "History": "History",
    "Horror": "Horror",
    "House garden": "House & Garden",
    "Independent": "Independent",
    "Kids family": "Kids & Family",
    "Lgbtq": "LGBTQ",
    "Music": "Music",
    "Musical": "Musical",
    "Mystery thriller": "Mystery & Thriller",
    "Nature": "Nature",
    "News": "News",
    "Other": "Other",
    "Reality": "Reality",
    "Romance": "Romance",
    "Sci fi": "Sci-Fi",
    "Short": "Short",
    "Soap": "Soap",
    "Special interest": "Special Interest",
    "Sports": "Sports & Fitness",
    "Stand up": "Stand Up",
    "Talk show": "Talk Show",
    "Travel": "Travel",
    "Variety": "Variety",
    "War": "War",
    "Western": "Western"
}

