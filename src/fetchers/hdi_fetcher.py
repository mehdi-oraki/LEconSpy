"""
HDI (Human Development Index) data fetcher from UN and Wikipedia
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


class HDIFetcher:
    """Fetches HDI data from multiple free sources."""

    def __init__(self):
        self.scraper = WebScraper()
        self.sources = DATA_SOURCES["hdi"]

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

    @staticmethod
    def _extract_country_values(df: pd.DataFrame, value_terms: List[str]) -> Dict[str, float]:
        if df.empty:
            return {}

        df = df.copy()
        flattened_columns = []
        for col in df.columns:
            if isinstance(col, tuple):
                pieces = [str(part) for part in col if part and str(part) != "nan"]
                flattened_columns.append(" ".join(pieces).strip())
            else:
                flattened_columns.append(str(col).strip())
        df.columns = flattened_columns

        country_column = next(
            (col for col in df.columns if any(term in col.lower() for term in ["country", "nation", "economy"])),
            df.columns[0],
        )

        value_column: Optional[str] = None
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

        if value_column is None:
            return {}

        df = df[[country_column, value_column]].dropna()

        data: Dict[str, float] = {}
        for _, row in df.iterrows():
            country = HDIFetcher._clean_country(row[country_column])
            if not country or country.lower() in {"world", "world average"}:
                continue

            value = row[value_column]
            try:
                value = float(value)
            except (TypeError, ValueError):
                match = re.search(r"0\.\d{3}", str(value))
                value = float(match.group()) if match else 0.0

            if 0 < value <= 1:
                data[country] = round(value, 3)

        return data

    def fetch_undp(self) -> Dict[str, float]:
        """Fetch HDI data from UNDP statistical annex (Excel download)."""
        logger.info("Fetching HDI data from UNDP...")
        url = self.sources["undp"]
        soup = self.scraper.fetch_html(url)
        if soup is None:
            logger.error("Failed to retrieve UNDP HDI page")
            return {}

        download_url: Optional[str] = None
        for link in soup.find_all("a", href=True):
            href = link.get("href", "")
            text = link.get_text(strip=True).lower()
            if ".xlsx" in href.lower() and any(term in text for term in ["table 1", "statistical annex", "hdi"]):
                download_url = href
                break

        if download_url is None:
            logger.warning("UNDP HDI Excel download link not found")
            return {}

        if not download_url.startswith("http"):
            download_url = urljoin(url, download_url)

        logger.info("Downloading UNDP HDI Excel dataset...")
        try:
            response = self.scraper.session.get(download_url, timeout=60)
            response.raise_for_status()
        except Exception as exc:
            logger.error(f"Failed to download UNDP HDI Excel file: {exc}")
            return {}

        try:
            excel_bytes = io.BytesIO(response.content)
            sheets = pd.read_excel(excel_bytes, sheet_name=None)
        except Exception as exc:
            logger.error(f"Could not parse UNDP HDI Excel data: {exc}")
            return {}

        value_terms = ["hdi", "index"]
        sources: List[Dict[str, float]] = []
        for sheet_name, sheet_df in sheets.items():
            extracted = self._extract_country_values(sheet_df, value_terms)
            if extracted:
                logger.info(f"Parsed {len(extracted)} countries from UNDP sheet '{sheet_name}'")
                sources.append(extracted)

        if not sources:
            logger.warning("UNDP HDI Excel parsing returned no usable data")
            return {}

        merged: Dict[str, float] = {}
        for source in sources:
            merged.update(source)

        logger.info(f"Fetched HDI data for {len(merged)} countries from UNDP")
        return merged

    def fetch_wikipedia(self) -> Dict[str, float]:
        """Fetch HDI data from Wikipedia."""
        logger.info("Fetching HDI data from Wikipedia...")
        url = self.sources["wikipedia"]
        soup = self.scraper.fetch_html(url)
        if soup is None:
            logger.error("Failed to retrieve Wikipedia HDI page")
            return {}

        tables = soup.find_all("table", {"class": "wikitable"})
        value_pattern = re.compile(r"0\.\d{3}")
        results: Dict[str, float] = {}

        for table in tables:
            headers = [
                self._clean_country(th.get_text(" ", strip=True))
                for th in table.find_all("th")
            ]
            if not any("HDI" in header.upper() for header in headers):
                continue

            rows = table.find_all("tr")
            if not rows:
                continue

            header_cells = rows[0].find_all(["th", "td"])
            country_idx: Optional[int] = None
            hdi_idx: Optional[int] = None

            for idx, cell in enumerate(header_cells):
                text = cell.get_text(" ", strip=True)
                upper_text = text.upper()
                if "HDI" in upper_text and "RANK" not in upper_text:
                    hdi_idx = idx
                if country_idx is None:
                    lower_text = text.lower()
                    if any(keyword in lower_text for keyword in ["country", "nation", "territory", "state"]):
                        country_idx = idx

            if country_idx is None:
                country_idx = 0

            if hdi_idx is None:
                continue

            for row in rows[1:]:
                cells = row.find_all(["td", "th"])
                if len(cells) <= hdi_idx or len(cells) <= country_idx:
                    continue
                country_raw = cells[country_idx].get_text(" ", strip=True)
                hdi_raw = cells[hdi_idx].get_text(" ", strip=True)

                country = self._clean_country(country_raw)
                if not country or country.lower() in {"world", "world average"}:
                    continue

                match = value_pattern.search(hdi_raw)
                if not match:
                    continue
                try:
                    value = float(match.group())
                except ValueError:
                    continue

                if 0 < value <= 1:
                    results[country] = round(value, 3)

            if results:
                logger.info(f"Parsed {len(results)} countries from Wikipedia HDI table")
                break

        if not results:
            logger.warning("No HDI values extracted from Wikipedia")
        return results

    def fetch_all(self) -> Dict[str, float]:
        """
        Fetch HDI data from free sources and reconcile results.

        Returns:
            Dict mapping country -> HDI value
        """
        sources: List[Dict[str, float]] = []

        undp_data = self.fetch_undp()
        if undp_data:
            sources.append({DataValidator.normalize_country_name(k): v for k, v in undp_data.items()})

        wikipedia_data = self.fetch_wikipedia()
        if wikipedia_data:
            sources.append(wikipedia_data)

        if not sources:
            logger.error("Failed to fetch HDI data from any source")
            return {}

        if len(sources) == 1:
            logger.warning("Only one HDI data source available; skipping validation")
            return sources[0]

        validated = DataValidator.validate_data(sources, "Human Development Index")
        reconciled: Dict[str, float] = {}
        for country, (value, confidence, is_valid) in validated.items():
            if is_valid or confidence >= 0.5:
                reconciled[DataValidator.normalize_country_name(country)] = round(value, 3)

        if not reconciled:
            logger.warning("HDI validation produced no high-confidence entries; falling back to primary source")
            return sources[0]

        logger.info(f"Validated HDI data for {len(reconciled)} countries")
        return reconciled

