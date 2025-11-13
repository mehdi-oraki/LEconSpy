"""
Data validation utilities for cross-checking data from multiple sources
"""

import logging
import re
from typing import Dict, List, Tuple, Optional

from config import VALIDATION_THRESHOLD

logger = logging.getLogger(__name__)


class DataValidator:
    """Validates and reconciles data from multiple sources"""
    
    @staticmethod
    def normalize_country_name(name: str) -> str:
        """
        Normalize country names for comparison
        
        Args:
            name: Country name to normalize
            
        Returns:
            Normalized country name
        """
        # Normalize whitespace and remove common suffixes / footnotes
        if not isinstance(name, str):
            name = str(name)

        name = name.replace("\u202f", " ").replace("\xa0", " ").replace("\u2009", " ")
        name = re.sub(r"\s+", " ", name)
        name = re.sub(r"\s*(\(\s*the\s*\))$", "", name, flags=re.IGNORECASE)
        name = re.sub(r"^(the\s+)", "", name, flags=re.IGNORECASE)
        name = re.sub(r"\s*[\*\u2020\u2021\u2022†‡]+$", "", name)
        name = name.strip()
        return name.title()
    
    @staticmethod
    def normalize_value(value: float) -> float:
        """
        Normalize numeric values (round to reasonable precision)
        
        Args:
            value: Numeric value to normalize
            
        Returns:
            Normalized value
        """
        return round(value, 2)
    
    @staticmethod
    def calculate_similarity(value1: float, value2: float) -> float:
        """
        Calculate similarity between two values (0-1 scale)
        
        Args:
            value1: First value
            value2: Second value
            
        Returns:
            Similarity score (0-1)
        """
        if value1 == 0 and value2 == 0:
            return 1.0
        if value1 == 0 or value2 == 0:
            return 0.0
        
        # Use relative difference
        diff = abs(value1 - value2)
        avg = (abs(value1) + abs(value2)) / 2
        similarity = 1 - (diff / avg) if avg > 0 else 0
        return max(0.0, min(1.0, similarity))
    
    @staticmethod
    def validate_data(
        data_sources: List[Dict[str, float]],
        metric_name: str
    ) -> Dict[str, Tuple[float, float, bool]]:
        """
        Validate data from multiple sources
        
        Args:
            data_sources: List of dicts with country -> value mappings
            metric_name: Name of the metric being validated
            
        Returns:
            Dict mapping country -> (validated_value, confidence, is_valid)
        """
        if len(data_sources) < 2:
            logger.warning(f"Insufficient sources for {metric_name}")
            return {}
        
        # Merge all country data
        all_countries = set()
        for source in data_sources:
            all_countries.update(source.keys())
        
        validated = {}
        
        for country in all_countries:
            values = []
            for source in data_sources:
                normalized_country = DataValidator.normalize_country_name(country)
                # Try exact match first
                if country in source:
                    values.append(source[country])
                elif normalized_country in source:
                    values.append(source[normalized_country])
                else:
                    # Try case-insensitive match
                    for key, value in source.items():
                        if key.lower() == country.lower():
                            values.append(value)
                            break
            
            if len(values) >= 2:
                # Calculate average and similarity
                avg_value = sum(values) / len(values)
                similarities = []
                for i in range(len(values)):
                    for j in range(i + 1, len(values)):
                        sim = DataValidator.calculate_similarity(values[i], values[j])
                        similarities.append(sim)
                
                avg_similarity = sum(similarities) / len(similarities) if similarities else 0
                is_valid = avg_similarity >= VALIDATION_THRESHOLD
                
                validated[country] = (
                    DataValidator.normalize_value(avg_value),
                    avg_similarity,
                    is_valid
                )
                
                if not is_valid:
                    logger.warning(
                        f"Low confidence for {country} {metric_name}: "
                        f"similarity={avg_similarity:.2f}, values={values}"
                    )
            elif len(values) == 1:
                # Single source - lower confidence
                validated[country] = (
                    DataValidator.normalize_value(values[0]),
                    0.5,
                    True
                )
        
        return validated

