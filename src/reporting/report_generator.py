"""
Report generator for Markdown, JSON, and HTML output
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import logging
from markdown import markdown as markdown_to_html

from config import OUTPUT_DIR
from src.reporting.visualizations import (
    generate_cost_of_living_trend_chart,
    generate_gdp_trend_chart,
)

logger = logging.getLogger(__name__)

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>Economic Intelligence Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 2rem;
            color: #1f2933;
            background-color: #f8fafc;
        }}
        h1, h2, h3 {{
            color: #0b7285;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin-bottom: 1.5rem;
        }}
        th, td {{
            border: 1px solid #cbd5e1;
            padding: 0.6rem;
            text-align: left;
        }}
        th {{
            background-color: #e0f2f1;
        }}
        tr:nth-child(even) td {{
            background-color: #f1f5f9;
        }}
        hr {{
            margin: 2rem 0;
            border: none;
            border-top: 1px solid #cbd5e1;
        }}
        .footer {{
            margin-top: 2rem;
            font-style: italic;
        }}
    </style>
</head>
<body>
{body}
</body>
</html>
"""


class ReportGenerator:
    """Generates reports in Markdown, JSON, and HTML formats."""

    def __init__(self) -> None:
        os.makedirs(OUTPUT_DIR, exist_ok=True)

    @staticmethod
    def _render_table_rows(
        rows: List[Tuple[str, float]],
        formatter: str,
        empty_message: str,
        precision: int = 2,
    ) -> List[str]:
        if not rows:
            return [empty_message]

        formatted: List[str] = []
        for idx, (country, value) in enumerate(rows, 1):
            if formatter == "currency":
                formatted.append(f"| {idx} | {country} | ${value:,.2f} |")
            elif formatter == "decimal":
                formatted.append(f"| {idx} | {country} | {value:.{precision}f} |")
            else:
                formatted.append(f"| {idx} | {country} | {value} |")
        return formatted

    def generate_markdown(
        self,
        state: Dict[str, Any],
        gdp_chart_html: Optional[str] = None,
        cost_chart_html: Optional[str] = None,
    ) -> str:
        """Generate Markdown report from agent state."""
        md: List[str] = []

        generated_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        md.append('<h1 align="center">Economic Intelligence Report</h1>')
        md.append("")
        md.append(f"**Generated:** {generated_ts}")
        md.append("")
        md.append("---")
        md.append("")

        # GDP Rankings
        md.append("## 1. GDP per Capita (PPP) Rankings")
        md.append("")
        md.append("### 1.1 Top 10 Countries")
        md.append("")
        md.append("| Rank | Country | GDP per Capita (PPP) |")
        md.append("|------|---------|----------------------|")
        md.extend(
            self._render_table_rows(
                state.get("gdp_top", [])[:10],
                formatter="currency",
                empty_message="| - | No data available | - |",
            )
        )
        md.append("")

        md.append("### 1.2 Bottom 10 Countries")
        md.append("")
        md.append("| Rank | Country | GDP per Capita (PPP) |")
        md.append("|------|---------|----------------------|")
        md.extend(
            self._render_table_rows(
                state.get("gdp_bottom", [])[:10],
                formatter="currency",
                empty_message="| - | No data available | - |",
            )
        )
        md.append("")

        cost_rows = state.get("cost_of_living_top_gdp", [])
        md.append("### 1.3 Cost of Living Index for Top GDP Countries")
        md.append("")
        missing_rows = state.get("cost_of_living_missing", [])
        if cost_rows:
            md.append("| Country | Cost of Living Index |")
            md.append("|---------|----------------------|")
            for country, value in cost_rows:
                md.append(f"| {country} | {value:.2f} |")
        else:
            md.append("_No cost of living data available for the current Top 10 GDP countries._")
        md.append("")
        if missing_rows:
            md.append(
                "_Missing cost of living entries for:_ "
                + ", ".join(missing_rows)
            )
            md.append("")

        md.append("### 1.4 Cost of Living Trend (Last 10 Years)")
        md.append("")
        if cost_chart_html:
            md.append("_Interactive chart — hover to inspect year-by-year changes._")
            md.append("")
            md.append(cost_chart_html)
        else:
            md.append("_Trend chart unavailable — insufficient historical CPI data from World Bank for the current selection._")
        md.append("")

        md.append("### 1.5 GDP per Capita Trend (Last 10 Years)")
        md.append("")
        if gdp_chart_html:
            md.append("_Interactive chart — hover to inspect year-by-year changes._")
            md.append("")
            md.append(gdp_chart_html)
        else:
            md.append("_Trend chart unavailable — insufficient historical GDP data from World Bank for the current selection._")
        md.append("")

        md.append("---")
        md.append("")

        # HDI Rankings
        md.append("## 2. Human Development Index (HDI) Rankings")
        md.append("")
        md.append("### 2.1 Top 10 Countries")
        md.append("")
        md.append("| Rank | Country | HDI Score |")
        md.append("|------|---------|-----------|")
        md.extend(
            self._render_table_rows(
                state.get("hdi_top", [])[:10],
                formatter="decimal",
                precision=3,
                empty_message="| - | No data available | - |",
            )
        )
        md.append("")

        md.append("### 2.2 Bottom 10 Countries")
        md.append("")
        md.append("| Rank | Country | HDI Score |")
        md.append("|------|---------|-----------|")
        md.extend(
            self._render_table_rows(
                state.get("hdi_bottom", [])[:10],
                formatter="decimal",
                precision=3,
                empty_message="| - | No data available | - |",
            )
        )
        md.append("")
        md.append("---")
        md.append("")

        # Happiness Rankings
        md.append("## 3. World Happiness Report Rankings")
        md.append("")
        md.append("### 3.1 Top 10 Countries")
        md.append("")
        md.append("| Rank | Country | Happiness Score |")
        md.append("|------|---------|----------------|")
        md.extend(
            self._render_table_rows(
                state.get("happiness_top", [])[:10],
                formatter="decimal",
                precision=3,
                empty_message="| - | No data available | - |",
            )
        )
        md.append("")

        md.append("### 3.2 Bottom 10 Countries")
        md.append("")
        md.append("| Rank | Country | Happiness Score |")
        md.append("|------|---------|----------------|")
        md.extend(
            self._render_table_rows(
                state.get("happiness_bottom", [])[:10],
                formatter="decimal",
                precision=3,
                empty_message="| - | No data available | - |",
            )
        )
        md.append("")
        md.append("---")
        md.append("")

        # Reality Check / Anomalies
        md.append("## 4. Reality Check: Hidden Patterns")
        md.append("")
        anomalies = state.get("anomalies", {}) or {}
        sections_rendered = False

        def fmt_metric(country: str, data: Dict[str, float], precision: int = 3) -> str:
            value = data.get(country)
            if value is None or value == 0:
                return "N/A"
            return f"{value:.{precision}f}"

        if anomalies.get("high_gdp_low_happiness"):
            sections_rendered = True
            md.append("### 4.1 High GDP but Low Happiness")
            md.append("")
            md.append("Countries with high GDP per capita but relatively low happiness scores:")
            md.append("")
            for country in anomalies["high_gdp_low_happiness"]:
                gdp = state.get("gdp_data", {}).get(country, 0)
                happiness = fmt_metric(country, state.get("happiness_data", {}))
                md.append(f"- **{country}**: GDP ${gdp:,.2f}, Happiness {happiness}")
            md.append("")

        if anomalies.get("high_hdi_low_gdp"):
            sections_rendered = True
            md.append("### 4.2 High HDI but Low GDP")
            md.append("")
            md.append("Countries with high human development but lower GDP per capita:")
            md.append("")
            for country in anomalies["high_hdi_low_gdp"]:
                hdi = fmt_metric(country, state.get("hdi_data", {}))
                gdp = state.get("gdp_data", {}).get(country, 0)
                md.append(f"- **{country}**: HDI {hdi}, GDP ${gdp:,.2f}")
            md.append("")

        if anomalies.get("high_happiness_low_gdp"):
            sections_rendered = True
            md.append("### 4.3 High Happiness but Low GDP")
            md.append("")
            md.append("Countries with high happiness scores despite lower GDP:")
            md.append("")
            for country in anomalies["high_happiness_low_gdp"]:
                happiness = fmt_metric(country, state.get("happiness_data", {}))
                gdp = state.get("gdp_data", {}).get(country, 0)
                md.append(f"- **{country}**: Happiness {happiness}, GDP ${gdp:,.2f}")
            md.append("")

        if anomalies.get("low_gdp_high_happiness"):
            sections_rendered = True
            md.append("### 4.4 Low GDP but High Happiness (Stable but Poor)")
            md.append("")
            md.append("Countries with low GDP but relatively high happiness (indicating stability despite poverty):")
            md.append("")
            for country in anomalies["low_gdp_high_happiness"]:
                gdp = state.get("gdp_data", {}).get(country, 0)
                happiness = fmt_metric(country, state.get("happiness_data", {}))
                md.append(f"- **{country}**: GDP ${gdp:,.2f}, Happiness {happiness}")
            md.append("")

        if not sections_rendered:
            md.append("_No significant anomalies detected based on current data._")
            md.append("")

        # Errors section
        errors = state.get("errors", [])
        if errors:
            md.append("---")
            md.append("")
            md.append("## 5. Errors and Warnings")
            md.append("")
            for error in errors:
                md.append(f"- ⚠️ {error}")
            md.append("")

        md.append("---")
        md.append("")
        md.append("*Report generated by LEconSpy - Zero-Cost Economic Intelligence System*")

        return "\n".join(md)

    def generate_json(self, state: Dict[str, Any], charts: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate JSON report from agent state."""
        timestamp = datetime.now().isoformat()
        return {
            "metadata": {"generated_at": timestamp, "version": "1.0.0"},
            "rankings": {
                "gdp_per_capita_ppp": {
                    "top_10": [
                        {"rank": idx, "country": country, "value": value}
                        for idx, (country, value) in enumerate(state.get("gdp_top", [])[:10], 1)
                    ],
                    "bottom_10": [
                        {"rank": idx, "country": country, "value": value}
                        for idx, (country, value) in enumerate(state.get("gdp_bottom", [])[:10], 1)
                    ],
                },
                "hdi": {
                    "top_10": [
                        {"rank": idx, "country": country, "value": value}
                        for idx, (country, value) in enumerate(state.get("hdi_top", [])[:10], 1)
                    ],
                    "bottom_10": [
                        {"rank": idx, "country": country, "value": value}
                        for idx, (country, value) in enumerate(state.get("hdi_bottom", [])[:10], 1)
                    ],
                },
                "happiness": {
                    "top_10": [
                        {"rank": idx, "country": country, "value": value}
                        for idx, (country, value) in enumerate(state.get("happiness_top", [])[:10], 1)
                    ],
                    "bottom_10": [
                        {"rank": idx, "country": country, "value": value}
                        for idx, (country, value) in enumerate(state.get("happiness_bottom", [])[:10], 1)
                    ],
                },
            },
            "anomalies": state.get("anomalies", {}),
            "errors": state.get("errors", []),
            "cost_of_living": {
                "top_gdp": [
                    {"country": country, "value": value}
                    for country, value in state.get("cost_of_living_top_gdp", [])
                ],
                "missing": state.get("cost_of_living_missing", []),
            },
            "charts": charts or {},
        }

    def generate_html(self, markdown_content: str) -> str:
        """Convert markdown content to an HTML page."""
        body = markdown_to_html(markdown_content, extensions=["tables"])
        return HTML_TEMPLATE.format(body=body)

    def save_reports(self, state: Dict[str, Any]) -> Tuple[str, str, str, str]:
        """Save Markdown, JSON, and HTML reports to disk."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        gdp_chart_html = generate_gdp_trend_chart(
            state.get("gdp_data", {}),
            state.get("gdp_top", []),
        )
        cost_chart_html = generate_cost_of_living_trend_chart(
            state.get("cost_of_living_data", {}),
            state.get("cost_of_living_top_gdp", []),
        )

        markdown_content = self.generate_markdown(
            state,
            gdp_chart_html=gdp_chart_html,
            cost_chart_html=cost_chart_html,
        )
        json_content = self.generate_json(
            state,
            charts={
                "gdp_per_capita_trend_html": gdp_chart_html,
                "cost_of_living_trend_html": cost_chart_html,
            },
        )
        html_content = self.generate_html(markdown_content)

        md_path = os.path.join(OUTPUT_DIR, f"economic_intelligence_report_{timestamp}.md")
        json_path = os.path.join(OUTPUT_DIR, f"economic_intelligence_report_{timestamp}.json")
        html_path = os.path.join(OUTPUT_DIR, f"economic_intelligence_report_{timestamp}.html")

        with open(md_path, "w", encoding="utf-8") as md_file:
            md_file.write(markdown_content)

        with open(json_path, "w", encoding="utf-8") as json_file:
            json.dump(json_content, json_file, indent=2, ensure_ascii=False)

        with open(html_path, "w", encoding="utf-8") as html_file:
            html_file.write(html_content)

        logger.info(f"Reports saved: {md_path}, {json_path}, {html_path}")

        return md_path, json_path, html_path, html_content

