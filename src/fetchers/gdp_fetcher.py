"""
GDP per capita (PPP) data fetcher using free public sources
"""

import logging
import re
from typing import Dict, List

import pandas as pd

from config import DATA_SOURCES
from src.utils.data_validator import DataValidator
from src.utils.web_scraper import WebScraper

logger = logging.getLogger(__name__)


class GDPFetcher:
    """Fetches GDP per capita (PPP) data from free sources"""

    def __init__(self):
        self.scraper = WebScraper()
        self.sources = DATA_SOURCES["gdp_ppp"]

    @staticmethod
    def _clean_numeric(value: str) -> float:
        """Extract numeric value from a text cell."""
        if value is None:
            return 0.0
        value = str(value)
        value = value.replace("\u202f", "")  # thin space
        match = re.search(r"[-+]?\d[\d,\s]*\.?\d*", value)
        if not match:
            return 0.0
        number = match.group().replace(",", "").replace(" ", "")
        try:
            return float(number)
        except ValueError:
            return 0.0

    @staticmethod
    def _clean_country(name: str) -> str:
        """Normalize country name by removing footnotes and extra text."""
        if not isinstance(name, str):
            name = str(name)
        name = name.replace("\u202f", " ").replace("\xa0", " ").replace("\u2009", " ")
        name = re.sub(r"\(.*?\)", "", name)
        name = re.sub(r"\[.*?\]", "", name)
        name = re.sub(r"\s*[\*\u2020\u2021\u2022†‡]+$", "", name)
        name = name.strip()
        return DataValidator.normalize_country_name(name)

    def _extract_country_values(self, df: pd.DataFrame, value_terms: List[str]) -> Dict[str, float]:
        """Extract country/value pairs from a DataFrame."""
        if df.empty:
            return {}

        df = df.copy()
        df.columns = [str(col).strip() for col in df.columns]

        country_column = next(
            (col for col in df.columns if any(term in col.lower() for term in ["country", "territory", "economy"])),
            df.columns[0],
        )

        value_column = None
        for col in df.columns:
            if col == country_column:
                continue
            lower_col = col.lower()
            if any(term in lower_col for term in value_terms):
                value_column = col
                break

        if value_column is None:
            numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
            if numeric_cols:
                value_column = numeric_cols[0]
            else:
                # Fallback: choose the column with the most numeric-looking values
                candidate_cols = [
                    col
                    for col in df.columns
                    if col != country_column and df[col].apply(lambda x: bool(re.search(r"\d", str(x)))).sum() > 0
                ]
                value_column = candidate_cols[0] if candidate_cols else None

        if value_column is None:
            return {}

        df = df[[country_column, value_column]].dropna()

        data: Dict[str, float] = {}
        for _, row in df.iterrows():
            country = self._clean_country(row[country_column])
            if not country or country.lower() in {"world", "world average", "world total"}:
                continue

            value = self._clean_numeric(row[value_column])
            if value > 0:
                data[country] = value

        return data

    def fetch_wikipedia_tables(self) -> List[Dict[str, float]]:
        """
        Fetch GDP per capita (PPP) data from multiple tables on Wikipedia.

        Returns:
            List of country/value mappings from different sources (IMF, World Bank, CIA)
        """
        logger.info("Fetching GDP per capita (PPP) tables from Wikipedia...")
        url = self.sources["wikipedia"]
        soup = self.scraper.fetch_html(url)
        if soup is None:
            logger.error("Failed to retrieve Wikipedia GDP page")
            return []

        try:
            tables = pd.read_html(str(soup))
        except ValueError as exc:
            logger.error(f"Could not parse Wikipedia GDP tables: {exc}")
            return []

        sources: List[Dict[str, float]] = []
        value_terms = [
            "int$",
            "per capita",
            "gdp",
            "ppp",
        ]

        for idx, table in enumerate(tables[:3]):  # IMF, World Bank, CIA tables
            extracted = self._extract_country_values(table, value_terms)
            if extracted:
                logger.info(f"Parsed {len(extracted)} countries from Wikipedia GDP table #{idx + 1}")
                sources.append(extracted)

        return sources

    def fetch_all(self) -> Dict[str, float]:
        """
        Fetch GDP data from free sources and reconcile them.

        Returns:
            Dict mapping country -> GDP per capita (PPP) value
        """
        data_sources = self.fetch_wikipedia_tables()

        if not data_sources:
            logger.error("GDP fetcher could not retrieve any data sources")
            return {}

        if len(data_sources) == 1:
            return data_sources[0]

        validated = DataValidator.validate_data(data_sources, "GDP per capita (PPP)")
        if not validated:
            logger.warning("GDP validation returned empty results, falling back to first source")
            return data_sources[0]

        reconciled: Dict[str, float] = {}
        for country, (value, confidence, is_valid) in validated.items():
            if is_valid or confidence >= 0.5:
                reconciled[DataValidator.normalize_country_name(country)] = value

        if not reconciled:
            logger.warning("GDP reconciliation produced no high-confidence entries; using primary source")
            return data_sources[0]

        logger.info(f"Validated GDP per capita (PPP) data for {len(reconciled)} countries")
        return reconciled

