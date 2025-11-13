<h1 align="center">Data Fetchers Directory</h1>

This directory contains data fetchers for different economic indicators.

## Files

### gdp_fetcher.py
Fetches GDP per capita (PPP) data:
- `GDPFetcher` class
- Methods: `fetch_world_bank()`, `fetch_wikipedia()`, `fetch_all()`
- Returns dictionary mapping country names to GDP values

### hdi_fetcher.py
Fetches Human Development Index (HDI) data:
- `HDIFetcher` class
- Methods: `fetch_undp()`, `fetch_wikipedia()`, `fetch_all()`
- Returns dictionary mapping country names to HDI values (0-1 scale)

### happiness_fetcher.py
Fetches World Happiness Report data:
- `HappinessFetcher` class
- Methods: `fetch_world_happiness_report()`, `fetch_wikipedia()`, `fetch_all()`
- Returns dictionary mapping country names to happiness scores

### cost_of_living_fetcher.py
Fetches cost of living index data:
- `CostOfLivingFetcher` class
- Method: `fetch()` retrieves cost of living indices from Wikipedia
- Returns dictionary mapping country names to cost of living index values

All fetchers use the `WebScraper` utility for HTTP requests and HTML parsing.

