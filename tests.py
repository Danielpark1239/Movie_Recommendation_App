import pytest
import scraping.scraper as scraper
from dotenv import load_dotenv

def test_scrapeMovies():
    load_dotenv()
    URLs = scraper.generateMovieURLs(
        [], [], [], 50, 50, 10, True
    )
    data = scraper.scrapeMovies(URLs, 50, 50, 10)
    assert data is not None


def test_scrapeTVshows():
    load_dotenv()
    URLs = scraper.generateTVshowURLs(
        [], [], [], 50, 50, 10, True
    )
    scraper.scrapeTVshows(URLs, 50, 50, 10)

def test_scrapeActor():
    load_dotenv()
    filterData = {
        "actorURL": 'https://www.rottentomatoes.com/celebrity/daniel_craig',
        "category": 'movie',
        "roles": 'all',
        "oldestYear": 2000,
        "boxOffice": 0,
        "genres": 'all',
        "ratings": 'all',
        "platforms": 'all',
        "tomatometerScore": 50,
        "audienceScore": 50,
        "limit": 10
    }
    scraper.scrapeActor(filterData)

def test_scrapeDirectorProducer():
    load_dotenv()
    filterData = {
        "url": 'https://www.rottentomatoes.com/celebrity/alfred_hitchcock',
        "category": 'movie',
        "oldestYear": 1900,
        "boxOffice": 0,
        "genres": 'all',
        "ratings": 'all',
        "platforms": 'all',
        "tomatometerScore": 50,
        "audienceScore": 50,
        "limit": 10
    }
    scraper.scrapeDirectorProducer(filterData, "director")

def test_scrapeSimilar():
    load_dotenv()
    filterData = {
        "url": 'https://www.rottentomatoes.com/tv/cyberpunk_edgerunners',
        "oldestYear": 2010,
        "platforms": 'all',
        "tomatometerScore": 50,
        "audienceScore": 50,
        "limit": 10
    }
    scraper.scrapeSimilar(filterData)