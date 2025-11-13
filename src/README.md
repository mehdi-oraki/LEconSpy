<h1 align="center">Source Code Directory</h1>

This directory contains the core source code for LEconSpy.

## Structure

### agents/
Contains the LangGraph agent network implementation:
- `econ_agent.py` - Main economic intelligence agent with workflow orchestration

### fetchers/
Data fetchers for different economic indicators:
- `gdp_fetcher.py` - Fetches GDP per capita (PPP) from World Bank and Wikipedia
- `hdi_fetcher.py` - Fetches HDI data from UNDP and Wikipedia
- `happiness_fetcher.py` - Fetches World Happiness Report data

### ranking/
Ranking algorithms and anomaly detection:
- `ranker.py` - Ranks countries and identifies economic anomalies

### reporting/
Report generation modules:
- `report_generator.py` - Generates Markdown and JSON reports

### utils/
Utility functions:
- `web_scraper.py` - Web scraping utilities with retry logic
- `data_validator.py` - Data validation and cross-checking functions

