<h1 align="center">LEconSpy - Zero-Cost Economic Intelligence System</h1>

## Table of Contents
- [1. Overview](#1-overview)
- [2. Data Sources](#2-data-sources)
- [3. Architecture](#3-architecture)
- [4. Installation](#4-installation)
- [5. Configuration (.env)](#5-configuration-env)
- [6. Usage](#6-usage)
- [7. Outputs](#7-outputs)
- [8. Project Structure](#8-project-structure)
- [9. Development Notes](#9-development-notes)
- [10. Git Workflow](#10-git-workflow)
- [11. License & Disclaimer](#11-license--disclaimer)

# 1. Overview
LEconSpy is a zero-cost economic intelligence system that:

- Fetches the latest economic indicators from free, trusted sources (World Bank, UNDP, World Happiness Report, Wikipedia, WorldPopulationReview).
- Validates metrics across multiple sources to maintain integrity.
- Ranks countries (Top 10 & Bottom 10) for each indicator and highlights hidden economic realities.
- Produces Markdown, JSON, and HTML reports with interactive charts.
- Runs 100% locally—no API keys, no paid subscriptions, and no hardcoded data.

## 1.1 Key Capabilities
- GDP per capita (PPP) ranking and 10-year trend analysis.
- Human Development Index (HDI) ranking.
- World Happiness ranking.
- Cost-of-living index alignment for the current GDP Top 10, including CPI-based historical trends where available.
- Automated “Reality Check” anomaly detection (e.g., high GDP but low happiness).

# 2. Data Sources
- **GDP per Capita (PPP)**: World Bank, Wikipedia.
- **HDI**: UNDP Statistical Annex, Wikipedia.
- **World Happiness Report**: World Happiness Report datasets, Wikipedia.
- **Cost of Living Index**: WorldPopulationReview, Wikipedia (fallback).
- **CPI (Cost-of-living trend)**: World Bank Consumer Price Index.

# 3. Architecture
## 3.1 LangGraph Workflow
1. Fetch GDP data.
2. Fetch HDI data.
3. Fetch Happiness data.
4. Rank metrics and derive Top/Bottom lists.
5. Fetch and align cost-of-living data for Top GDP countries.
6. Build anomaly insights.

## 3.2 Validation Pipeline
- Normalises country names across sources.
- Computes similarity scores between indicators.
- Flags inconsistencies and surfaces missing entries for transparency.

# 4. Installation
1. Clone the repository:
```bash
git clone <repository-url>
cd LEconSpy
```
2. Install dependencies:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

# 5. Configuration (.env)
The application reads optional overrides from `.env`. Copy the template below into a local `.env` file:
```dotenv
USER_AGENT="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
REQUEST_TIMEOUT=30
REQUEST_RETRIES=3
OUTPUT_DIR=output
CACHE_DIR=cache
MIN_SOURCES_FOR_VALIDATION=2
VALIDATION_THRESHOLD=0.95
```
> `.env` remains git-ignored—keep any personal overrides private.

# 6. Usage
Run the main entry point to execute the full pipeline:
```bash
python main.py
```
The workflow:
1. Fetches and validates datasets.
2. Ranks GDP, HDI, and Happiness metrics.
3. Aligns cost-of-living data with the GDP Top 10 (report lists any missing countries).
4. Generates trend charts (GDP PPP and CPI) when historical coverage exists.
5. Writes Markdown, JSON, and HTML reports to `output/`.

# 7. Outputs
After each run you will find:

1. **Markdown Report** (`output/economic_intelligence_report_YYYYMMDD_HHMMSS.md`)
   - Ranked tables for all indicators.
   - Cost-of-living alignment table and transparency on missing entries.
   - Interactive charts embedded (rendered in compatible Markdown viewers).
   - Reality check anomaly summaries.

2. **JSON Report** (`output/economic_intelligence_report_YYYYMMDD_HHMMSS.json`)
   - Machine-friendly representation of rankings, anomalies, chart HTML, and cost-of-living coverage.

3. **HTML Report** (`output/economic_intelligence_report_YYYYMMDD_HHMMSS.html`)
   - Fully styled report with embedded Plotly charts; open in a browser for interaction.

# 8. Project Structure
```
LEconSpy/
├── main.py
├── config.py
├── requirements.txt
├── src/
│   ├── agents/
│   │   └── econ_agent.py
│   ├── fetchers/
│   │   ├── gdp_fetcher.py
│   │   ├── hdi_fetcher.py
│   │   ├── happiness_fetcher.py
│   │   └── cost_of_living_fetcher.py
│   ├── ranking/
│   │   └── ranker.py
│   ├── reporting/
│   │   └── report_generator.py
│   └── utils/
│       ├── web_scraper.py
│       └── data_validator.py
└── output/ (generated reports)
```

# 9. Development Notes
- Free datasets often omit microstates (e.g., Monaco, Liechtenstein, Bermuda). Reports list any missing cost-of-living entries so you can manually supplement or substitute alternate countries.
- Trend charts rely on World Bank CPI and GDP PPP. If insufficient history exists, the chart section explains the omission.
- `python-dotenv` loads automatically; environment overrides only require adding keys to `.env`.

# 10. Git Workflow
Use the following process to push changes to GitHub:
1. **Check status**
   ```bash
   git status
   ```
2. **Stage changes**
   ```bash
   git add <files>
   ```
3. **Review staged diff**
   ```bash
   git diff --staged
   ```
4. **Commit with a semantic message**
   ```bash
   git commit -m "feat: describe your change"
   ```
5. **Push to remote**
   ```bash
   git push origin <branch-name>
   ```
6. **Open a pull request** (if using feature branches) and merge after review.

# 11. License & Disclaimer
This project is intended for educational and research purposes. Respect the terms of service of all upstream data providers. Results should be interpreted with an understanding of data quality, update cadence, and geopolitical context. The system is provided as-is without warranty.

