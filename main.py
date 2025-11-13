"""
LEconSpy - Zero-Cost Economic Intelligence System
Main entry point for the LangGraph agent network
"""

import logging
import sys
from src.agents.econ_agent import EconomicIntelligenceAgent
from src.reporting.report_generator import ReportGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Main execution function"""
    logger.info("=" * 60)
    logger.info("LEconSpy - Zero-Cost Economic Intelligence System")
    logger.info("=" * 60)
    logger.info("")
    
    try:
        # Initialize agent
        logger.info("Initializing Economic Intelligence Agent...")
        agent = EconomicIntelligenceAgent()
        
        # Run agent workflow
        logger.info("Executing agent workflow...")
        state = agent.run()
        
        # Generate reports
        logger.info("Generating reports...")
        report_generator = ReportGenerator()
        md_path, json_path, html_path, html_content = report_generator.save_reports(state)
        
        # Print summary
        logger.info("")
        logger.info("=" * 60)
        logger.info("EXECUTION COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Markdown report: {md_path}")
        logger.info(f"JSON report: {json_path}")
        logger.info(f"HTML report: {html_path}")
        logger.info("")
        
        # Print quick summary
        logger.info("Quick Summary:")
        logger.info(f"  - GDP data: {len(state.get('gdp_data', {}))} countries")
        logger.info(f"  - HDI data: {len(state.get('hdi_data', {}))} countries")
        logger.info(f"  - Happiness data: {len(state.get('happiness_data', {}))} countries")
        
        errors = state.get("errors", [])
        if errors:
            logger.warning(f"  - Errors encountered: {len(errors)}")
            for error in errors:
                logger.warning(f"    * {error}")
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("")

        logger.info("Open the HTML report locally for the full interactive view.")
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("\nExecution interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())

