"""
Evaluation Module for LangSmith Integration

This module provides LangSmith evaluation logging and post-execution metadata 
integration for the GenAI Training Transcript Generator.

Key Components:
- EvaluationLogger: Core logging interface for workflow executions
- LangSmithIntegration: Post-execution metadata transmission
- RAGEvaluator: Knowledge retrieval evaluation (future enhancement)
"""

from .config import LangSmithConfig, get_default_config, validate_environment
from .langsmith_integration import LangSmithIntegration
from .langsmith_logger import EvaluationLogger

__all__ = ['EvaluationLogger', 'LangSmithConfig', 'LangSmithIntegration', 'get_default_config', 'validate_environment']