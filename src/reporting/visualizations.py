"""
Visualization helpers for economic intelligence reports.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict, Iterable, List, Optional, Tuple

import plotly.graph_objects as go
import requests

from src.utils.data_validator import DataValidator

logger = logging.getLogger(__name__)


class WorldBankClient:
    """Minimal World Bank API client for fetching indicator time series."""

    BASE_URL = "https://api.worldbank.org/v2"
    INDICATOR_GDP_PPP = "NY.GDP.PCAP.PP.CD"
    INDICATOR_CPI = "FP.CPI.TOTL"

    def __init__(self) -> None:
        self.session = requests.Session()
        self._country_codes: Optional[Dict[str, str]] = None

    def _ensure_country_codes(self) -> None:
        if self._country_codes is not None:
            return

        url = f"{self.BASE_URL}/country?format=json&per_page=400"
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            payload = response.json()
        except requests.RequestException as exc:
            logger.warning("Failed to fetch World Bank country codes: %s", exc)
            self._country_codes = {}
            return

        data = payload[1] if isinstance(payload, list) and len(payload) > 1 else []
        mapping: Dict[str, str] = {}
        for entry in data:
            name = entry.get("name")
            iso3 = entry.get("id")
            if not name or not iso3:
                continue
            normalized = DataValidator.normalize_country_name(name)
            mapping[normalized] = iso3.lower()

        self._country_codes = mapping

    def lookup_codes(self, countries: Iterable[str]) -> Dict[str, str]:
        """Return ISO-3 codes for the requested country names."""
        self._ensure_country_codes()
        if not self._country_codes:
            return {}

        codes: Dict[str, str] = {}
        for country in countries:
            normalized = DataValidator.normalize_country_name(country)
            code = self._country_codes.get(normalized)
            if code:
                codes[country] = code
        return codes

    def fetch_indicator_timeseries(
        self,
        iso_codes: Iterable[str],
        indicator: str,
        start_year: int,
        end_year: int,
    ) -> Dict[str, List[Tuple[int, Optional[float]]]]:
        """Fetch indicator values for the given ISO codes and year range."""
        cleaned = [code.lower() for code in iso_codes if code]
        if not cleaned:
            return {}

        codes = ";".join(sorted(set(cleaned)))
        url = (
            f"{self.BASE_URL}/country/{codes}/indicator/{indicator}"
            f"?format=json&per_page=20000&date={start_year}:{end_year}"
        )
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            payload = response.json()
        except requests.RequestException as exc:
            logger.warning("Failed to fetch World Bank indicator %s: %s", indicator, exc)
            return {}

        data = payload[1] if isinstance(payload, list) and len(payload) > 1 else []
        series: Dict[str, List[Tuple[int, Optional[float]]]] = {}
        for entry in data:
            country_info = entry.get("country") or {}
            country_name = country_info.get("value")
            year = entry.get("date")
            value = entry.get("value")
            if not country_name or not year:
                continue

            try:
                year_int = int(year)
            except ValueError:
                continue

            normalized_name = DataValidator.normalize_country_name(country_name)
            series.setdefault(normalized_name, []).append((year_int, value))

        for country, values in series.items():
            values.sort(key=lambda item: item[0])
        return series


def _select_candidate_countries(
    gdp_data: Dict[str, float],
    focus_countries: List[Tuple[str, float]],
    max_candidates: int,
) -> List[str]:
    ordered: List[str] = []
    seen: set[str] = set()

    for country, _ in focus_countries:
        normalized = DataValidator.normalize_country_name(country)
        if normalized not in seen:
            ordered.append(country)
            seen.add(normalized)
        if len(ordered) >= max_candidates:
            return ordered

    sorted_gdp = sorted(gdp_data.items(), key=lambda item: item[1], reverse=True)
    for country, _ in sorted_gdp:
        normalized = DataValidator.normalize_country_name(country)
        if normalized in seen:
            continue
        ordered.append(country)
        seen.add(normalized)
        if len(ordered) >= max_candidates:
            break

    return ordered


def generate_gdp_trend_chart(
    gdp_data: Dict[str, float],
    gdp_top: List[Tuple[str, float]],
    years: int = 10,
    max_countries: int = 8,
    min_traces: int = 3,
) -> Optional[str]:
    """Create an interactive chart of GDP (PPP) trends for the strongest countries."""
    if not gdp_data and not gdp_top:
        return None

    client = WorldBankClient()
    candidates = _select_candidate_countries(gdp_data, gdp_top[:10], max_countries * 2)
    if not candidates:
        return None

    country_codes = client.lookup_codes(candidates)
    if not country_codes:
        logger.warning("Could not resolve World Bank codes for GDP trend chart")
        return None

    ordered_with_codes = [country for country in candidates if country in country_codes]
    if not ordered_with_codes:
        logger.warning("No candidate countries matched World Bank codes for chart")
        return None

    selected_countries = ordered_with_codes[:max_countries]

    current_year = datetime.now().year
    start_year = current_year - (years - 1)
    end_year = current_year

    indicator_data = client.fetch_indicator_timeseries(
        iso_codes=[country_codes[country] for country in selected_countries],
        indicator=client.INDICATOR_GDP_PPP,
        start_year=start_year,
        end_year=end_year,
    )

    if not indicator_data:
        logger.warning("No indicator data returned for GDP trend chart")
        return None

    fig = go.Figure()
    traces_added = 0

    for country in selected_countries:
        normalized = DataValidator.normalize_country_name(country)
        series = indicator_data.get(normalized)
        if not series:
            continue

        filtered = [(year, value) for year, value in series if value is not None]
        if len(filtered) < 2:
            continue

        years_list = [year for year, _ in filtered]
        values_list = [value for _, value in filtered]

        fig.add_trace(
            go.Scatter(
                x=years_list,
                y=values_list,
                mode="lines+markers",
                name=country,
                hovertemplate="<b>%{fullData.name}</b><br>Year: %{x}<br>GDP: $%{y:,.0f}<extra></extra>",
            )
        )
        traces_added += 1

    if traces_added < min_traces:
        logger.warning("Insufficient GDP trend data (only %s traces)", traces_added)
        return None

    fig.update_layout(
        title="GDP per Capita (PPP) — 10-Year Trend",
        xaxis_title="Year",
        yaxis_title="GDP per Capita (PPP, current international $)",
        hovermode="x unified",
        template="plotly_white",
        legend_title_text="Country",
    )

    return fig.to_html(full_html=False, include_plotlyjs="cdn")


def generate_cost_of_living_trend_chart(
    cost_data: Dict[str, float],
    focus_countries: List[Tuple[str, float]],
    years: int = 10,
    max_countries: int = 8,
    min_traces: int = 3,
) -> Optional[str]:
    """Create an interactive chart of CPI (proxy for cost of living)."""
    if not focus_countries:
        return None

    client = WorldBankClient()
    candidates = _select_candidate_countries(cost_data, focus_countries, max_countries * 2)
    if not candidates:
        return None

    country_codes = client.lookup_codes(candidates)
    if not country_codes:
        logger.warning("Could not resolve codes for cost of living chart")
        return None

    ordered_with_codes = [country for country in candidates if country in country_codes]
    if not ordered_with_codes:
        return None

    selected_countries = ordered_with_codes[:max_countries]

    current_year = datetime.now().year
    start_year = current_year - (years - 1)
    end_year = current_year

    indicator_data = client.fetch_indicator_timeseries(
        iso_codes=[country_codes[country] for country in selected_countries],
        indicator=client.INDICATOR_CPI,
        start_year=start_year,
        end_year=end_year,
    )

    if not indicator_data:
        logger.warning("No CPI data returned for cost of living chart")
        return None

    fig = go.Figure()
    traces_added = 0

    for country in selected_countries:
        normalized = DataValidator.normalize_country_name(country)
        series = indicator_data.get(normalized)
        if not series:
            continue

        filtered = [(year, value) for year, value in series if value is not None]
        if len(filtered) < 2:
            continue

        filtered.sort(key=lambda item: item[0])
        years_list = [year for year, _ in filtered]
        values_list = [value for _, value in filtered]

        fig.add_trace(
            go.Scatter(
                x=years_list,
                y=values_list,
                mode="lines+markers",
                name=country,
                hovertemplate="<b>%{fullData.name}</b><br>Year: %{x}<br>CPI: %{y:.2f}<extra></extra>",
            )
        )
        traces_added += 1

    if traces_added < min_traces:
        logger.warning("Insufficient cost of living trend data (only %s traces)", traces_added)
        return None

    fig.update_layout(
        title="Cost of Living (CPI, 2010=100) — 10-Year Trend",
        xaxis_title="Year",
        yaxis_title="Consumer Price Index (2010 = 100)",
        hovermode="x unified",
        template="plotly_white",
        legend_title_text="Country",
    )

    return fig.to_html(full_html=False, include_plotlyjs="cdn")


