<h1 align="center">Utilities Directory</h1>

This directory contains utility functions used throughout the system.

## Files

### web_scraper.py
Web scraping utilities:

- **WebScraper** class:
  - `fetch_html()`: Fetches and parses HTML content
  - `fetch_json()`: Fetches JSON data
  - `fetch_csv()`: Fetches CSV content
  - Includes retry logic with exponential backoff
  - Proper user-agent headers for web requests

### data_validator.py
Data validation and cross-checking:

- **DataValidator** class with static methods:
  - `normalize_country_name()`: Normalizes country names for comparison
  - `normalize_value()`: Normalizes numeric values
  - `calculate_similarity()`: Calculates similarity between values
  - `validate_data()`: Cross-validates data from multiple sources

Uses configurable similarity thresholds to ensure data quality.

