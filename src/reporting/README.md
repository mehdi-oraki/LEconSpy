<h1 align="center">Reporting Directory</h1>

This directory contains report generation modules.

## Files

### report_generator.py
Generates reports in multiple formats:

- **ReportGenerator** class:
  - `generate_markdown()`: Creates formatted Markdown report with tables
  - `generate_json()`: Creates structured JSON report
  - `save_reports()`: Saves both formats to output directory

Reports include:
- Rankings for all three metrics (Top 10 & Bottom 10)
- Reality check analysis with anomalies
- Error and warning information
- Metadata (generation timestamp, version)

