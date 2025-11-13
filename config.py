"""
Configuration settings for LEconSpy - Economic Intelligence System
"""

# type: ignore

import os

from dotenv import load_dotenv

load_dotenv()

# Data source URLs
DATA_SOURCES = {
    "gdp_ppp": {
        "world_bank": "https://data.worldbank.org/indicator/NY.GDP.PCAP.PP.CD",
        "wikipedia": "https://en.wikipedia.org/wiki/List_of_countries_by_GDP_(PPP)_per_capita"
    },
    "hdi": {
        "undp": "http://hdr.undp.org/en/content/human-development-index-hdi",
        "wikipedia": "https://en.wikipedia.org/wiki/List_of_countries_by_Human_Development_Index"
    },
    "happiness": {
        "world_happiness": "https://worldhappiness.report/data/",
        "wikipedia": "https://en.wikipedia.org/wiki/World_Happiness_Report#2024_World_Happiness_Report"
    },
    "cost_of_living": {
        "wikipedia": "https://en.wikipedia.org/wiki/List_of_countries_by_cost_of_living",
        "wpr": "https://worldpopulationreview.com/country-rankings/cost-of-living-by-country"
    }
}

# User agent for web requests
USER_AGENT = os.getenv(
    "USER_AGENT",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
)

# Request settings
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
REQUEST_RETRIES = int(os.getenv("REQUEST_RETRIES", "3"))

# Output settings
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")
CACHE_DIR = os.getenv("CACHE_DIR", "cache")

# Validation settings
MIN_SOURCES_FOR_VALIDATION = int(os.getenv("MIN_SOURCES_FOR_VALIDATION", "2"))
VALIDATION_THRESHOLD = float(os.getenv("VALIDATION_THRESHOLD", "0.95"))  # 95% similarity threshold for cross-validation

