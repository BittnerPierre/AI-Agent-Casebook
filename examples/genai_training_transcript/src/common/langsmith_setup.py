"""
Centralized LangSmith tracing setup for all agents
"""

import os
import logging

logger = logging.getLogger(__name__)

# Global flag to track if tracing has been set up
_TRACING_CONFIGURED = False

def configure_langsmith_tracing():
    """
    Configure LangSmith tracing globally for all agents.
    
    Returns:
        bool: True if tracing was successfully configured, False otherwise
    """
    global _TRACING_CONFIGURED
    
    if _TRACING_CONFIGURED:
        logger.debug("LangSmith tracing already configured")
        return True
    
    langsmith_api_key = os.getenv('LANGSMITH_API_KEY')
    langsmith_project = os.getenv('LANGSMITH_PROJECT', 'story-ops')
    langsmith_tracing = os.getenv('LANGSMITH_TRACING', '').lower() == 'true'
    
    if not langsmith_api_key:
        logger.debug("LANGSMITH_API_KEY not found. LangSmith tracing disabled.")
        return False
        
    if not langsmith_tracing:
        logger.debug("LANGSMITH_TRACING not enabled. LangSmith tracing disabled.")
        return False
    
    try:
        # Import here to avoid circular imports
        from agents import set_trace_processors
        from langsmith.wrappers import OpenAIAgentsTracingProcessor
        
        # Set up trace processors globally
        os.environ['LANGSMITH_API_KEY'] = langsmith_api_key
        os.environ['LANGSMITH_PROJECT'] = langsmith_project
        
        # Configure trace processor
        set_trace_processors([OpenAIAgentsTracingProcessor()])
        
        _TRACING_CONFIGURED = True
        logger.info(f"LangSmith tracing configured globally for project: {langsmith_project}")
        return True
        
    except Exception as e:
        logger.warning(f"Failed to configure LangSmith tracing: {e}")
        return False

def is_tracing_enabled():
    """Check if LangSmith tracing is enabled"""
    return _TRACING_CONFIGURED