"""
LangSmith Configuration for US-007 and US-012

This module provides configuration management for LangSmith integration
including project settings, environment variable handling, and default values.

Key Features:
- Environment variable validation
- Configuration defaults for "story-ops" project
- Kebab-case naming convention support
- Integration status checking

Author: Claude Code - Sprint 1 Week 3
Reference: US-007 LangSmith Evaluation Logging & US-012 Post-Execution Metadata
"""

import os
from dataclasses import dataclass
from typing import Any


@dataclass
class LangSmithConfig:
    """Configuration class for LangSmith integration"""
    
    # Core LangSmith settings
    api_key: str | None = None
    project_name: str = "story-ops"
    endpoint: str = "https://api.smith.langchain.com"
    
    # Evaluation logging settings (US-007)
    enable_evaluation_logging: bool = True
    auto_send_metadata: bool = True
    log_agent_conversations: bool = True
    
    # Agent SDK tracing settings (US-012)
    enable_auto_trace: bool = True
    trace_level: str = "detailed"
    include_inputs: bool = True
    include_outputs: bool = True
    include_metadata: bool = True
    
    # Performance settings
    retry_attempts: int = 3
    batch_size: int = 10
    flush_interval_seconds: int = 30
    
    # Naming convention settings
    use_kebab_case: bool = True
    run_name_prefix: str = "transcript-generation"
    
    @classmethod
    def from_environment(cls) -> 'LangSmithConfig':
        """Create configuration from environment variables"""
        
        return cls(
            api_key=os.getenv('LANGSMITH_API_KEY'),
            project_name=os.getenv('LANGSMITH_PROJECT', 'story-ops'),
            endpoint=os.getenv('LANGSMITH_ENDPOINT', 'https://api.smith.langchain.com'),
            
            # Evaluation logging settings
            enable_evaluation_logging=_parse_bool(os.getenv('LANGSMITH_ENABLE_LOGGING', 'true')),
            auto_send_metadata=_parse_bool(os.getenv('LANGSMITH_AUTO_SEND', 'true')),
            log_agent_conversations=_parse_bool(os.getenv('LANGSMITH_LOG_CONVERSATIONS', 'true')),
            
            # Agent SDK tracing settings  
            enable_auto_trace=_parse_bool(os.getenv('LANGSMITH_AUTO_TRACE', 'true')),
            trace_level=os.getenv('LANGSMITH_TRACE_LEVEL', 'detailed'),
            include_inputs=_parse_bool(os.getenv('LANGSMITH_INCLUDE_INPUTS', 'true')),
            include_outputs=_parse_bool(os.getenv('LANGSMITH_INCLUDE_OUTPUTS', 'true')),
            include_metadata=_parse_bool(os.getenv('LANGSMITH_INCLUDE_METADATA', 'true')),
            
            # Performance settings
            retry_attempts=int(os.getenv('LANGSMITH_RETRY_ATTEMPTS', '3')),
            batch_size=int(os.getenv('LANGSMITH_BATCH_SIZE', '10')),
            flush_interval_seconds=int(os.getenv('LANGSMITH_FLUSH_INTERVAL', '30')),
            
            # Naming convention settings
            use_kebab_case=_parse_bool(os.getenv('LANGSMITH_USE_KEBAB_CASE', 'true')),
            run_name_prefix=os.getenv('LANGSMITH_RUN_PREFIX', 'transcript-generation')
        )
    
    def is_fully_configured(self) -> bool:
        """Check if LangSmith is fully configured and ready to use"""
        return (
            self.api_key is not None and
            len(self.api_key.strip()) > 0 and
            self.project_name is not None and
            len(self.project_name.strip()) > 0
        )
    
    def get_integration_status(self) -> dict[str, Any]:
        """Get current integration status for monitoring"""
        return {
            "api_key_configured": self.api_key is not None,
            "project_name": self.project_name,
            "endpoint": self.endpoint,
            "evaluation_logging_enabled": self.enable_evaluation_logging,
            "auto_trace_enabled": self.enable_auto_trace,
            "fully_configured": self.is_fully_configured(),
            "config_source": "environment" if self.api_key else "defaults"
        }
    
    def get_agent_sdk_config(self) -> dict[str, Any]:
        """Get configuration dictionary for Agent SDK tracing"""
        return {
            "project_name": self.project_name,
            "auto_trace": self.enable_auto_trace,
            "trace_level": self.trace_level,
            "include_inputs": self.include_inputs,
            "include_outputs": self.include_outputs,
            "include_metadata": self.include_metadata,
            "kebab_case_naming": self.use_kebab_case,
            "batch_size": self.batch_size,
            "flush_interval": self.flush_interval_seconds
        }
    
    def get_run_name(self, suffix: str = "") -> str:
        """Generate run name following kebab-case convention"""
        base_name = self.run_name_prefix
        
        if suffix:
            if self.use_kebab_case:
                # Convert to kebab-case
                suffix = suffix.lower().replace('_', '-').replace(' ', '-')
                return f"{base_name}-{suffix}"
            else:
                return f"{base_name}_{suffix}"
        
        return base_name


def _parse_bool(value: str | None) -> bool:
    """Parse string environment variable to boolean"""
    if value is None:
        return False
    return value.lower() in ('true', '1', 'yes', 'on', 'enabled')


def get_default_config() -> LangSmithConfig:
    """Get default LangSmith configuration from environment"""
    return LangSmithConfig.from_environment()


def validate_environment() -> dict[str, Any]:
    """
    Validate LangSmith environment configuration.
    
    Returns:
        Dictionary with validation results and recommendations
    """
    config = get_default_config()
    
    validation_result = {
        "valid": True,
        "warnings": [],
        "errors": [],
        "recommendations": []
    }
    
    # Check API key
    if not config.api_key:
        validation_result["warnings"].append("LANGSMITH_API_KEY not set - LangSmith logging will be disabled")
        validation_result["recommendations"].append("Set LANGSMITH_API_KEY environment variable to enable logging")
    
    # Check project name
    if not config.project_name or config.project_name == "story-ops":
        validation_result["recommendations"].append("Using default project 'story-ops' - consider customizing LANGSMITH_PROJECT")
    
    # Check trace settings consistency
    if config.enable_auto_trace and not config.api_key:
        validation_result["warnings"].append("Auto-trace enabled but no API key - tracing will not work")
    
    # Performance recommendations
    if config.retry_attempts > 5:
        validation_result["warnings"].append(f"High retry attempts ({config.retry_attempts}) may impact performance")
    
    if config.batch_size > 50:
        validation_result["warnings"].append(f"Large batch size ({config.batch_size}) may cause memory issues")
    
    # Overall validity
    validation_result["valid"] = len(validation_result["errors"]) == 0
    validation_result["fully_configured"] = config.is_fully_configured()
    
    return validation_result


# Module-level default configuration
DEFAULT_CONFIG = get_default_config()