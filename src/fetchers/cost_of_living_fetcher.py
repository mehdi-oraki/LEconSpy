"""
Cost of living data fetcher from free public sources.
"""

from __future__ import annotations

import logging
import re
from typing import Dict, List, Optional

import pandas as pd

from config import DATA_SOURCES
from src.utils.data_validator import DataValidator
from src.utils.web_scraper import WebScraper

logger = logging.getLogger(__name__)


class CostOfLivingFetcher:
    """Fetches cost of living indices from free sources."""

    def __init__(self) -> None:
        self.scraper = WebScraper()
        sources = DATA_SOURCES["cost_of_living"]
        self.wikipedia_source = sources["wikipedia"]
        self.wpr_source = sources["wpr"]

    @staticmethod
    def _clean_country(name: str) -> str:
        cleaned = re.sub(r"\[.*?\]", "", name)
        cleaned = re.sub(r"\(.*?\)", "", cleaned)
        cleaned = cleaned.replace("\u202f", " ").replace("\xa0", " ")
        return DataValidator.normalize_country_name(cleaned.strip())

    @staticmethod
    def _clean_value(value: str) -> float:
        value = str(value)
        match = re.search(r"[-+]?[0-9]*\.?[0-9]+", value.replace(",", ""))
        if not match:
            return 0.0
        try:
            return float(match.group())
        except ValueError:
            return 0.0

    @staticmethod
    def _flatten_columns(columns: pd.Index) -> List[str]:
        flattened: List[str] = []
        if isinstance(columns, pd.MultiIndex):
            for col in columns:
                pieces = [str(part) for part in col if part and str(part) != "nan"]
                flattened.append(" ".join(pieces).strip().lower())
        else:
            flattened = [str(col).strip().lower() for col in columns]
        return flattened

    def _parse_tables(self, tables: List[pd.DataFrame]) -> Optional[Dict[str, float]]:
        for table in tables:
            lower_columns = self._flatten_columns(table.columns)
            if not any("cost" in col and "index" in col for col in lower_columns):
                continue

            df = table.copy()
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [
                    " ".join([str(part) for part in col if part and str(part) != "nan"]).strip()
                    for col in df.columns
                ]
            else:
                df.columns = [str(col).strip() for col in df.columns]

            country_col = None
            index_col = None
            for col in df.columns:
                lower = col.lower()
                if country_col is None and any(keyword in lower for keyword in ["country", "nation", "territory"]):
                    country_col = col
                if index_col is None and "cost" in lower and "index" in lower:
                    index_col = col

            if country_col is None or index_col is None:
                continue

            data: Dict[str, float] = {}
            for _, row in df.dropna(subset=[country_col, index_col]).iterrows():
                country = self._clean_country(row[country_col])
                if not country:
                    continue
                value = self._clean_value(row[index_col])
                if value <= 0:
                    continue
                data[country] = value

            if data:
                return data
        return None

    def fetch(self) -> Dict[str, float]:
        """Fetch cost of living index data from public sources."""
        logger.info("Fetching cost of living data from World Population Review...")
        soup = self.scraper.fetch_html(self.wpr_source)
        if soup:
            try:
                tables = pd.read_html(str(soup))
            except ValueError as exc:
                logger.warning("Failed to parse WPR cost of living tables: %s", exc)
            else:
                parsed = self._parse_tables(tables)
                if parsed:
                    logger.info("Parsed cost of living data for %s countries (WPR)", len(parsed))
                    return parsed

        logger.info("Falling back to Wikipedia cost of living dataset...")
        soup = self.scraper.fetch_html(self.wikipedia_source)
        if not soup:
            logger.error("Failed to retrieve Wikipedia cost of living page")
            return {}

        try:
            tables = pd.read_html(str(soup))
        except ValueError as exc:
            logger.error("Failed to parse Wikipedia cost of living tables: %s", exc)
            return {}

        parsed = self._parse_tables(tables)
        if parsed:
            logger.info("Parsed cost of living data for %s countries (Wikipedia)", len(parsed))
            return parsed

        logger.warning("No suitable cost of living table found on available sources")
        return {}
