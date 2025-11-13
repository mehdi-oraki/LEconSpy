<h1 align="center">Agents Directory</h1>

This directory contains the LangGraph agent network implementation.

## Files

### econ_agent.py
Main economic intelligence agent that orchestrates the entire workflow:

- **EconomicIntelligenceAgent**: Main agent class
- **AgentState**: TypedDict defining the agent state structure
- Workflow steps:
  1. Fetch GDP data
  2. Fetch HDI data
  3. Fetch happiness data
  4. Rank countries
  5. Find anomalies

The agent uses LangGraph's StateGraph to manage the workflow state and transitions.

