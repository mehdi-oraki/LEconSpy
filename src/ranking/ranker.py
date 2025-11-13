"""
Ranking module for top 10 and bottom 10 countries
"""

import logging
from typing import Dict, List, Tuple
from operator import itemgetter

logger = logging.getLogger(__name__)


class Ranker:
    """Ranks countries by economic indicators"""
    
    @staticmethod
    def rank_countries(
        data: Dict[str, float],
        metric_name: str,
        top_n: int = 10,
        bottom_n: int = 10
    ) -> Tuple[List[Tuple[str, float]], List[Tuple[str, float]]]:
        """
        Rank countries by metric value
        
        Args:
            data: Dict mapping country -> value
            metric_name: Name of the metric
            top_n: Number of top countries to return
            bottom_n: Number of bottom countries to return
            
        Returns:
            Tuple of (top_countries, bottom_countries) as lists of (country, value) tuples
        """
        if not data:
            logger.warning(f"No data available for {metric_name}")
            return [], []
        
        # Sort by value (descending for top, ascending for bottom)
        sorted_countries = sorted(data.items(), key=itemgetter(1), reverse=True)
        
        # Get top N
        top_countries = sorted_countries[:top_n]
        
        # Get bottom N (reverse order for readability)
        bottom_countries = sorted(sorted_countries[-bottom_n:], key=itemgetter(1), reverse=True)
        
        logger.info(
            f"Ranked {metric_name}: Top={len(top_countries)}, Bottom={len(bottom_countries)}"
        )
        
        return top_countries, bottom_countries
    
    @staticmethod
    def find_anomalies(
        gdp_data: Dict[str, float],
        hdi_data: Dict[str, float],
        happiness_data: Dict[str, float]
    ) -> Dict[str, List[str]]:
        """
        Find interesting anomalies and patterns in the data
        
        Args:
            gdp_data: GDP per capita (PPP) data
            hdi_data: HDI data
            happiness_data: Happiness score data
            
        Returns:
            Dict with anomaly categories and countries
        """
        anomalies = {
            "high_gdp_low_happiness": [],
            "high_hdi_low_gdp": [],
            "high_happiness_low_gdp": [],
            "low_gdp_high_happiness": []
        }
        
        # Get all countries present in at least 2 datasets
        all_countries = set(gdp_data.keys()) | set(hdi_data.keys()) | set(happiness_data.keys())
        
        # Calculate thresholds (median values)
        gdp_values = [v for v in gdp_data.values() if v > 0]
        hdi_values = [v for v in hdi_data.values() if 0 < v <= 1]
        happiness_values = [v for v in happiness_data.values() if v > 0]
        
        gdp_median = sorted(gdp_values)[len(gdp_values) // 2] if gdp_values else 0
        hdi_median = sorted(hdi_values)[len(hdi_values) // 2] if hdi_values else 0
        happiness_median = sorted(happiness_values)[len(happiness_values) // 2] if happiness_values else 0
        
        for country in all_countries:
            gdp = gdp_data.get(country, 0)
            hdi = hdi_data.get(country, 0)
            happiness = happiness_data.get(country, 0)
            
            # High GDP but low happiness
            if gdp > gdp_median * 1.5 and happiness > 0 and happiness < happiness_median * 0.8:
                anomalies["high_gdp_low_happiness"].append(country)
            
            # High HDI but low GDP growth (we can't measure growth, so skip this)
            # Instead: High HDI but low GDP
            if hdi > hdi_median * 1.2 and gdp > 0 and gdp < gdp_median * 0.7:
                anomalies["high_hdi_low_gdp"].append(country)
            
            # High happiness but low GDP
            if happiness > happiness_median * 1.2 and gdp > 0 and gdp < gdp_median * 0.7:
                anomalies["high_happiness_low_gdp"].append(country)
            
            # Low GDP but high happiness (stable but poor)
            if gdp > 0 and gdp < gdp_median * 0.5 and happiness > happiness_median * 1.1:
                anomalies["low_gdp_high_happiness"].append(country)
        
        return anomalies

