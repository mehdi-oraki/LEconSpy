"""
LangGraph agent network for economic intelligence gathering
"""

import logging
from typing import Dict, Any, TypedDict
from langgraph.graph import StateGraph, END
from src.fetchers.gdp_fetcher import GDPFetcher
from src.fetchers.hdi_fetcher import HDIFetcher
from src.fetchers.happiness_fetcher import HappinessFetcher
from src.fetchers.cost_of_living_fetcher import CostOfLivingFetcher
from src.ranking.ranker import Ranker
from src.utils.data_validator import DataValidator

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """State for the economic intelligence agent"""
    gdp_data: Dict[str, float]
    hdi_data: Dict[str, float]
    happiness_data: Dict[str, float]
    cost_of_living_data: Dict[str, float]
    gdp_top: list
    gdp_bottom: list
    hdi_top: list
    hdi_bottom: list
    happiness_top: list
    happiness_bottom: list
    cost_of_living_top_gdp: list
    cost_of_living_missing: list
    anomalies: Dict[str, list]
    errors: list
    step: str


class EconomicIntelligenceAgent:
    """Main LangGraph agent for economic intelligence gathering"""
    
    def __init__(self):
        self.gdp_fetcher = GDPFetcher()
        self.hdi_fetcher = HDIFetcher()
        self.happiness_fetcher = HappinessFetcher()
        self.cost_of_living_fetcher = CostOfLivingFetcher()
        self.ranker = Ranker()
        self.validator = DataValidator()
        
        # Build the graph
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("fetch_gdp", self._fetch_gdp)
        workflow.add_node("fetch_hdi", self._fetch_hdi)
        workflow.add_node("fetch_happiness", self._fetch_happiness)
        workflow.add_node("rank_data", self._rank_data)
        workflow.add_node("fetch_cost_of_living", self._fetch_cost_of_living)
        workflow.add_node("find_anomalies", self._find_anomalies)
        
        # Set entry point
        workflow.set_entry_point("fetch_gdp")
        
        # Define edges
        workflow.add_edge("fetch_gdp", "fetch_hdi")
        workflow.add_edge("fetch_hdi", "fetch_happiness")
        workflow.add_edge("fetch_happiness", "rank_data")
        workflow.add_edge("rank_data", "fetch_cost_of_living")
        workflow.add_edge("fetch_cost_of_living", "find_anomalies")
        workflow.add_edge("find_anomalies", END)
        
        return workflow.compile()
    
    def _fetch_gdp(self, state: AgentState) -> AgentState:
        """Fetch GDP data"""
        logger.info("Agent: Fetching GDP data...")
        state["step"] = "fetching_gdp"
        try:
            gdp_data = self.gdp_fetcher.fetch_all()
            state["gdp_data"] = gdp_data
            logger.info(f"Agent: Fetched GDP data for {len(gdp_data)} countries")
        except Exception as e:
            logger.error(f"Agent: Error fetching GDP data: {e}")
            state["gdp_data"] = {}
            if "errors" not in state:
                state["errors"] = []
            state["errors"].append(f"GDP fetch error: {str(e)}")
        return state
    
    def _fetch_hdi(self, state: AgentState) -> AgentState:
        """Fetch HDI data"""
        logger.info("Agent: Fetching HDI data...")
        state["step"] = "fetching_hdi"
        try:
            hdi_data = self.hdi_fetcher.fetch_all()
            state["hdi_data"] = hdi_data
            logger.info(f"Agent: Fetched HDI data for {len(hdi_data)} countries")
        except Exception as e:
            logger.error(f"Agent: Error fetching HDI data: {e}")
            state["hdi_data"] = {}
            if "errors" not in state:
                state["errors"] = []
            state["errors"].append(f"HDI fetch error: {str(e)}")
        return state
    
    def _fetch_happiness(self, state: AgentState) -> AgentState:
        """Fetch happiness data"""
        logger.info("Agent: Fetching happiness data...")
        state["step"] = "fetching_happiness"
        try:
            happiness_data = self.happiness_fetcher.fetch_all()
            state["happiness_data"] = happiness_data
            logger.info(f"Agent: Fetched happiness data for {len(happiness_data)} countries")
        except Exception as e:
            logger.error(f"Agent: Error fetching happiness data: {e}")
            state["happiness_data"] = {}
            if "errors" not in state:
                state["errors"] = []
            state["errors"].append(f"Happiness fetch error: {str(e)}")
        return state
    
    def _rank_data(self, state: AgentState) -> AgentState:
        """Rank countries for each metric"""
        logger.info("Agent: Ranking countries...")
        state["step"] = "ranking"
        
        try:
            # Rank GDP
            gdp_top, gdp_bottom = self.ranker.rank_countries(
                state.get("gdp_data", {}),
                "GDP per capita (PPP)"
            )
            state["gdp_top"] = gdp_top
            state["gdp_bottom"] = gdp_bottom
            
            # Rank HDI
            hdi_top, hdi_bottom = self.ranker.rank_countries(
                state.get("hdi_data", {}),
                "HDI"
            )
            state["hdi_top"] = hdi_top
            state["hdi_bottom"] = hdi_bottom
            
            # Rank Happiness
            happiness_top, happiness_bottom = self.ranker.rank_countries(
                state.get("happiness_data", {}),
                "World Happiness Report"
            )
            state["happiness_top"] = happiness_top
            state["happiness_bottom"] = happiness_bottom
            
            logger.info("Agent: Ranking completed")
        except Exception as e:
            logger.error(f"Agent: Error ranking data: {e}")
            if "errors" not in state:
                state["errors"] = []
            state["errors"].append(f"Ranking error: {str(e)}")
        
        return state

    def _fetch_cost_of_living(self, state: AgentState) -> AgentState:
        """Fetch cost of living data and align with top GDP countries."""
        logger.info("Agent: Fetching cost of living data...")
        state["step"] = "fetching_cost_of_living"

        try:
            cost_data = self.cost_of_living_fetcher.fetch()
            state["cost_of_living_data"] = cost_data

            gdp_top = state.get("gdp_top", [])
            if gdp_top and cost_data:
                normalized_lookup = {
                    DataValidator.normalize_country_name(country): (country, value)
                    for country, value in cost_data.items()
                }
                aligned: list = []
                missing: list = []
                for country, _ in gdp_top[:10]:
                    normalized = DataValidator.normalize_country_name(country)
                    if normalized in normalized_lookup:
                        original_name, value = normalized_lookup[normalized]
                        aligned.append((country, value))
                    else:
                        missing.append(country)
                state["cost_of_living_top_gdp"] = aligned
                state["cost_of_living_missing"] = missing
            else:
                state["cost_of_living_top_gdp"] = []
                state["cost_of_living_missing"] = gdp_top[:10] if gdp_top else []

            logger.info(
                "Agent: Cost of living data aligned for %s countries",
                len(state.get("cost_of_living_top_gdp", [])),
            )
        except Exception as e:
            logger.error(f"Agent: Error fetching cost of living data: {e}")
            state["cost_of_living_data"] = {}
            state["cost_of_living_top_gdp"] = []
            state["cost_of_living_missing"] = []
            if "errors" not in state:
                state["errors"] = []
            state["errors"].append(f"Cost of living fetch error: {str(e)}")

        return state
    
    def _find_anomalies(self, state: AgentState) -> AgentState:
        """Find interesting anomalies in the data"""
        logger.info("Agent: Finding anomalies...")
        state["step"] = "finding_anomalies"
        
        try:
            anomalies = self.ranker.find_anomalies(
                state.get("gdp_data", {}),
                state.get("hdi_data", {}),
                state.get("happiness_data", {})
            )
            state["anomalies"] = anomalies
            logger.info("Agent: Anomaly detection completed")
        except Exception as e:
            logger.error(f"Agent: Error finding anomalies: {e}")
            state["anomalies"] = {}
            if "errors" not in state:
                state["errors"] = []
            state["errors"].append(f"Anomaly detection error: {str(e)}")
        
        return state
    
    def run(self) -> AgentState:
        """Execute the agent workflow"""
        logger.info("Starting Economic Intelligence Agent...")
        initial_state: AgentState = {
            "gdp_data": {},
            "hdi_data": {},
            "happiness_data": {},
            "cost_of_living_data": {},
            "gdp_top": [],
            "gdp_bottom": [],
            "hdi_top": [],
            "hdi_bottom": [],
            "happiness_top": [],
            "happiness_bottom": [],
            "cost_of_living_top_gdp": [],
            "cost_of_living_missing": [],
            "anomalies": {},
            "errors": [],
            "step": "initialized"
        }
        
        result = self.graph.invoke(initial_state)
        logger.info("Economic Intelligence Agent completed")
        return result

