<h1 align="center">Ranking Directory</h1>

This directory contains ranking algorithms and anomaly detection.

## Files

### ranker.py
Ranking and anomaly detection module:

- **Ranker** class with static methods:
  - `rank_countries()`: Ranks countries by metric value (Top N and Bottom N)
  - `find_anomalies()`: Identifies interesting patterns:
    - High GDP but low happiness
    - High HDI but low GDP
    - High happiness but low GDP
    - Low GDP but high happiness (stable but poor)

Returns ranked lists and anomaly categories for report generation.

