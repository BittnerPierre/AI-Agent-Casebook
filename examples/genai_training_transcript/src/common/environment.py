"""
Environment Configuration Management

Centralized environment variable loading and configuration for the transcript generator.
Handles .env loading gracefully and provides consistent access to environment variables.
"""

import inspect
import os
from typing import Optional


class EnvironmentConfig:
    """
    Singleton for centralized environment configuration.
    
    Automatically loads .env file if available, falls back to system environment variables.
    Provides safe access to configuration values needed by different modules.
    """
    
    _instance: Optional['EnvironmentConfig'] = None
    _loaded: bool = False
    
    def __new__(cls) -> 'EnvironmentConfig':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._loaded:
            self._load_environment()
            self._loaded = True
    
    def _load_environment(self) -> None:
        """Load environment variables from .env file if available"""
        try:
            from dotenv import load_dotenv, find_dotenv
            env_file = find_dotenv()
            if env_file:
                load_dotenv(env_file)
                print(f"✅ Environment variables loaded from {env_file}")
            else:
                print("ℹ️  No .env file found, using system environment variables only")
        except ImportError:
            print("⚠️  python-dotenv not available, using system environment variables only")
    
    @property
    def openai_api_key(self) -> Optional[str]:
        """Get OpenAI API key from environment"""
        return os.environ.get('OPENAI_API_KEY')
    
    @property
    def langsmith_api_key(self) -> Optional[str]:
        """Get LangSmith API key from environment"""
        return os.environ.get('LANGSMITH_API_KEY')
    
    @property
    def langsmith_project(self) -> str:
        """Get LangSmith project name from environment"""
        return os.environ.get('LANGSMITH_PROJECT', 'story-ops')
    
    @property
    def langsmith_tracing_enabled(self) -> bool:
        """Check if LangSmith tracing is enabled"""
        return os.environ.get('LANGSMITH_TRACING', '').lower() == 'true'
    
    @property
    def is_openai_available(self) -> bool:
        """Check if OpenAI configuration is available"""
        return bool(self.openai_api_key)
    
    @property
    def is_langsmith_available(self) -> bool:
        """Check if LangSmith configuration is available"""
        return bool(self.langsmith_api_key)
    
    @property
    def is_openai_agents_available(self) -> bool:
        """
        Check if OpenAI Agents SDK is available and properly configured.
        
        This replaces the fragile _AGENTS_SDK_AVAILABLE pattern by checking:
        1. OpenAI Agents SDK is importable
        2. OpenAI API key is configured  
        3. Runner.run is a coroutine function (expected API)
        """
        if not self.is_openai_available:
            return False
            
        try:
            from agents import Agent, Runner
            # Verify the expected API interface
            run_method = getattr(Runner, 'run', None)
            return inspect.iscoroutinefunction(run_method)
        except ImportError:
            return False
    
    def get_debug_info(self) -> dict:
        """Get debug information about current configuration"""
        return {
            'openai_available': self.is_openai_available,
            'langsmith_available': self.is_langsmith_available,
            'agents_available': self.is_openai_agents_available,
            'langsmith_tracing': self.langsmith_tracing_enabled,
            'langsmith_project': self.langsmith_project,
            'openai_api_key': '✅ Set' if self.openai_api_key else '❌ Missing',
            'langsmith_api_key': '✅ Set' if self.langsmith_api_key else '❌ Missing'
        }


# Global singleton instance
env_config = EnvironmentConfig() 