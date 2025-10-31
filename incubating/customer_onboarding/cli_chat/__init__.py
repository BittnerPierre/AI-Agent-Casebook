"""
Package CLI Chat

CLI générique et configurable pour tester des agents conversationnels 
et générer des datasets d'évaluation avec annotations.
"""

from .core import ChatSession, ChatCLI
from .base_wrapper import BaseAgentWrapper, SimpleAgentWrapper
from .config import (
    DEFAULT_CONVERSATION_STARTERS,
    DEFAULT_OUTPUT_DIR,
    INTERFACE_MESSAGES,
    VALIDATION_MESSAGES,
    FORMATTING
)

__all__ = [
    # Core components
    "ChatSession",
    "ChatCLI",
    
    # Agent wrappers
    "BaseAgentWrapper", 
    "SimpleAgentWrapper",
    
    # Configuration
    "DEFAULT_CONVERSATION_STARTERS",
    "DEFAULT_OUTPUT_DIR",
    "INTERFACE_MESSAGES",
    "VALIDATION_MESSAGES",
    "FORMATTING"
]
