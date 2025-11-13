"""
World Happiness Report data fetcher
"""

import io
import logging
import re
from typing import Dict, List, Optional
from urllib.parse import urljoin

import pandas as pd

from config import DATA_SOURCES
from src.utils.data_validator import DataValidator
from src.utils.web_scraper import WebScraper

logger = logging.getLogger(__name__)


class HappinessFetcher:
    """Fetches World Happiness Report data."""

    def __init__(self):
        self.scraper = WebScraper()
        self.sources = DATA_SOURCES["happiness"]

    @staticmethod
    def _clean_country(name: str) -> str:
        if not isinstance(name, str):
            name = str(name)
        name = name.replace("\u202f", " ").replace("\xa0", " ").replace("\u2009", " ")
        name = re.sub(r"\s+", " ", name)
        name = re.sub(r"\(.*?\)", "", name)
        name = re.sub(r"\[.*?\]", "", name)
        name = re.sub(r"\s*[\*\u2020\u2021\u2022†‡]+$", "", name)
        return DataValidator.normalize_country_name(name.strip())


    def fetch_world_happiness_report(self) -> Dict[str, float]:
        """Fetch happiness data from the official World Happiness Report site."""
        logger.info("Fetching happiness data from World Happiness Report...")
        url = self.sources["world_happiness"]
        soup = self.scraper.fetch_html(url)
        if soup is None:
            logger.error("Failed to retrieve World Happiness Report page")
            return {}

        csv_links: List[str] = []
        for link in soup.find_all("a", href=True):
            href = link.get("href", "")
            text = link.get_text(strip=True).lower()
            if ".csv" in href.lower() and any(term in text for term in ["download", "data", "table", "appendix"]):
                csv_links.append(href)

        if not csv_links:
            logger.warning("No CSV links found on World Happiness Report page")
            return {}

        for raw_link in csv_links:
            download_url = raw_link
            if not download_url.startswith("http"):
                download_url = urljoin(url, download_url)

            logger.info(f"Attempting to download World Happiness Report dataset: {download_url}")
            csv_content = self.scraper.fetch_csv(download_url)
            if not csv_content:
                continue

            try:
                df = pd.read_csv(io.StringIO(csv_content))
            except Exception as exc:
                logger.warning(f"Failed to parse CSV from {download_url}: {exc}")
                continue

            # Identify country and score columns
            columns_lower = [col.lower() for col in df.columns]
            country_col = next(
                (col for col in df.columns if any(term in col.lower() for term in ["country", "nation"])),
                None,
            )
            score_col = next(
                (
                    col
                    for col in df.columns
                    if any(term in col.lower() for term in ["ladder", "score", "cantril"])
                ),
                None,
            )

            if country_col is None or score_col is None:
                logger.debug(f"CSV from {download_url} did not contain expected columns")
                continue

            df = df[[country_col, score_col]].dropna()
            data = {}
            for _, row in df.iterrows():
                country = self._clean_country(row[country_col])
                try:
                    value = float(row[score_col])
                except (TypeError, ValueError):
                    continue

                if 1 <= value <= 9:
                    data[country] = round(value, 3)

            if data:
                logger.info(f"Fetched happiness data for {len(data)} countries from official dataset")
                return data

        logger.warning("All official World Happiness Report downloads failed to parse")
        return {}

    def fetch_wikipedia(self) -> Dict[str, float]:
        """Fetch happiness data from Wikipedia tables."""
        logger.info("Fetching happiness data from Wikipedia...")
        url = self.sources["wikipedia"]
        soup = self.scraper.fetch_html(url)
        if soup is None:
            logger.error("Failed to retrieve Wikipedia happiness page")
            return {}

        tables = soup.find_all("table", {"class": "wikitable"})
        score_pattern = re.compile(r"\d+\.\d+")
        results: Dict[str, float] = {}

        for table in tables:
            rows = table.find_all("tr")
            if len(rows) < 2:
                continue

            header_cells = rows[0].find_all(["th", "td"])
            country_idx: Optional[int] = None
            score_idx: Optional[int] = None

            for idx, cell in enumerate(header_cells):
                text = cell.get_text(" ", strip=True).lower()
                if any(keyword in text for keyword in ["score", "ladder", "happiness"]):
                    score_idx = idx
                if country_idx is None:
                    if any(keyword in text for keyword in ["country", "nation", "territory", "state"]):
                        country_idx = idx

            if country_idx is None:
                country_idx = 0

            if score_idx is None:
                continue

            for row in rows[1:]:
                cells = row.find_all(["td", "th"])
                if len(cells) <= score_idx or len(cells) <= country_idx:
                    continue

                country_raw = cells[country_idx].get_text(" ", strip=True)
                score_raw = cells[score_idx].get_text(" ", strip=True)
                country = self._clean_country(country_raw)
                if not country:
                    continue

                match = score_pattern.search(score_raw)
                if not match:
                    continue
                try:
                    value = float(match.group())
                except ValueError:
                    continue

                if 1 <= value <= 9:
                    results[country] = round(value, 3)

            if results:
                logger.info(f"Parsed {len(results)} countries from Wikipedia happiness table")
                break

        if not results:
            logger.warning("No happiness values extracted from Wikipedia")
        return results

    def fetch_all(self) -> Dict[str, float]:
        """
        Fetch happiness data from free sources and reconcile results.

        Returns:
            Dict mapping country -> Happiness score
        """
        sources: List[Dict[str, float]] = []

        official_data = self.fetch_world_happiness_report()
        if official_data:
            sources.append({DataValidator.normalize_country_name(k): v for k, v in official_data.items()})

        wikipedia_data = self.fetch_wikipedia()
        if wikipedia_data:
            sources.append(wikipedia_data)

        if not sources:
            logger.error("Failed to fetch happiness data from any source")
            return {}

        if len(sources) == 1:
            logger.warning("Only one happiness data source available; skipping validation")
            return sources[0]

        validated = DataValidator.validate_data(sources, "World Happiness Report")
        reconciled: Dict[str, float] = {}
        for country, (value, confidence, is_valid) in validated.items():
            if is_valid or confidence >= 0.5:
                reconciled[DataValidator.normalize_country_name(country)] = round(value, 3)

        if not reconciled:
            logger.warning("Happiness validation produced no high-confidence entries; falling back to primary source")
            return sources[0]

        logger.info(f"Validated happiness data for {len(reconciled)} countries")
        return reconciled

