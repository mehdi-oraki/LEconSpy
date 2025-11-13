<h1 align="center">Quick Start Guide</h1>

## Installation

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Verify setup:**
```bash
python verify_setup.py
```

3. **Run the system:**
```bash
python main.py
```

## What It Does

The system will:

1. Fetch economic data from free public sources
2. Validate data across multiple sources
3. Rank countries (Top 10 & Bottom 10) for:
   - GDP per capita (PPP)
   - Human Development Index (HDI)
   - World Happiness Report Score
4. Identify economic anomalies and patterns
5. Generate reports in `output/` directory

## Output Files

After running, check the `output/` directory for:

- `economic_intelligence_report_YYYYMMDD_HHMMSS.md` - Markdown report
- `economic_intelligence_report_YYYYMMDD_HHMMSS.json` - JSON data
- `economic_intelligence_report_YYYYMMDD_HHMMSS.html` - Styled HTML report (also printed to the console)
- Each report embeds interactive 10-year trend charts for GDP per capita and cost of living (CPI) covering the current Top 10 GDP countries.

## Troubleshooting

### Import Errors

If you get import errors for LangGraph:
```bash
pip install --upgrade langgraph langchain
```

### Network Issues

The system fetches data from public websites. If you encounter network errors:
- Check your internet connection
- Some sources may have rate limiting - wait a few minutes and try again
- Wikipedia tables may change structure - the system will attempt to adapt

### No Data Retrieved

If no data is retrieved:
- Check that source websites are accessible
- Verify your firewall/proxy settings
- Some sources may require different parsing - check logs for details

## Customization

Edit `config.py` to customize:
- Data source URLs
- Request timeouts
- Validation thresholds
- Output directories

