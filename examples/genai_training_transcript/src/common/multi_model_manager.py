"""
Multi-Model Manager for US-016: Multi-Model Support via LiteLLM

Provides unified access to multiple AI model providers (OpenAI, Anthropic, Mistral)
with cost optimization and intelligent model selection.

Based on LiteLLM integration pattern from experiments/onboarding/main.py

Author: Claude Code - US-016 Multi-Model Support
Reference: Cost optimization and vendor flexibility
"""

import logging
import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

try:
    from agents.extensions.models.litellm_model import LitellmModel
except ImportError:
    raise ImportError(
        "LiteLLM model not available. Ensure agents SDK is installed with LiteLLM support."
    )

# Setup logging
logger = logging.getLogger(__name__)


class ModelTier(Enum):
    """Model capability tiers for different task types"""
    FAST = "fast"          # Fast inference for simple tasks
    BALANCED = "balanced"  # Balanced performance for general tasks
    REASONING = "reasoning" # Advanced reasoning for complex tasks
    FALLBACK = "fallback"  # Backup when primary unavailable


class ModelProvider(Enum):
    """Supported model providers"""
    MISTRAL = "mistral"
    ANTHROPIC = "anthropic"
    OPENAI = "openai"


@dataclass
class ModelConfig:
    """Configuration for a specific model"""
    name: str
    provider: ModelProvider
    tier: ModelTier
    cost_per_token: float = 0.0
    max_tokens: int = 4096
    supports_function_calling: bool = True
    supports_streaming: bool = True
    reasoning_capable: bool = False  # New: indicates reasoning capability
    use_cases: list = None          # New: list of recommended use cases
    description: str = ""           # New: human-readable description
    api_key_env: str = ""
    
    def __post_init__(self):
        if not self.api_key_env:
            self.api_key_env = f"{self.provider.value.upper()}_API_KEY"
        if self.use_cases is None:
            self.use_cases = []


@dataclass 
class AgentModelConfig:
    """Model configuration for a specific agent type"""
    name: str
    role: str  # planner, researcher, writer, evaluator, etc.
    primary_model: str
    fallback_model: str | None = None
    provider: str = "mistral"
    reasoning_required: bool = False    # New: whether this agent needs reasoning
    tools: list = field(default_factory=list)
    mcp_servers: list = field(default_factory=list)
    handoff_targets: list = field(default_factory=list)
    instructions_template: str = ""


class MultiModelManager:
    """
    Manages multiple AI model providers with intelligent selection and fallback.
    
    Features:
    - Unified interface across OpenAI, Anthropic, and Mistral
    - Cost-optimized model selection
    - Automatic fallback mechanisms
    - Agent-level model configuration
    - Environment-based overrides
    """
    
    def __init__(self, config_path: str | None = None):
        """
        Initialize MultiModelManager with model configurations.
        
        Args:
            config_path: Path to YAML configuration file (optional)
        """
        self.logger = logging.getLogger(__name__)
        
        # Default model configurations
        self._model_configs = self._create_default_model_configs()
        
        # Agent configurations
        self._agent_configs = self._create_default_agent_configs()
        
        # Load custom configuration if provided
        if config_path and os.path.exists(config_path):
            self._load_config_file(config_path)
        else:
            # Try to load default models_config.yaml if it exists
            default_config = Path(__file__).parent.parent.parent / "models_config.yaml"
            if default_config.exists():
                self._load_config_file(str(default_config))
        
        # Apply environment overrides
        self._apply_env_overrides()
        
        self.logger.info(f"MultiModelManager initialized with {len(self._model_configs)} model configs")
    
    def _create_default_model_configs(self) -> dict[str, ModelConfig]:
        """Create default model configurations"""
        return {
            # Mistral Models
            "mistral-small-latest": ModelConfig(
                name="mistral-small-latest",
                provider=ModelProvider.MISTRAL,
                tier=ModelTier.FAST,
                cost_per_token=0.000002,
                max_tokens=32768,
                supports_function_calling=True,
                reasoning_capable=False,
                use_cases=["research", "writing", "simple_tasks"],
                description="Fast and cost-effective for simple tasks"
            ),
            "mistral-medium-latest": ModelConfig(
                name="mistral-medium-latest", 
                provider=ModelProvider.MISTRAL,
                tier=ModelTier.BALANCED,
                cost_per_token=0.000006,
                max_tokens=32768,
                supports_function_calling=True,
                reasoning_capable=False,
                use_cases=["content_generation", "editing", "moderate_complexity"],
                description="Balanced performance for general tasks"
            ),
            "magistral-medium-latest": ModelConfig(
                name="magistral-medium-latest", 
                provider=ModelProvider.MISTRAL,
                tier=ModelTier.REASONING,
                cost_per_token=0.000006,
                max_tokens=32768,
                supports_function_calling=True,
                reasoning_capable=True,
                use_cases=["planning", "evaluation", "complex_reasoning"],
                description="Reasoning model for complex planning and evaluation"
            ),
            
            # Anthropic Models
            "claude-sonnet-4-0": ModelConfig(
                name="claude-sonnet-4-0",
                provider=ModelProvider.ANTHROPIC,
                tier=ModelTier.REASONING,
                cost_per_token=0.000015,
                max_tokens=200000,
                supports_function_calling=True,
                reasoning_capable=True,
                use_cases=["planning", "evaluation", "complex_reasoning"],
                description="Advanced reasoning model for sophisticated tasks"
            ),
            "claude-3-5-haiku-latest": ModelConfig(
                name="claude-3-5-haiku-latest",
                provider=ModelProvider.ANTHROPIC, 
                tier=ModelTier.FAST,
                cost_per_token=0.000001,
                max_tokens=200000,
                supports_function_calling=True,
                reasoning_capable=False,
                use_cases=["research", "quick_responses", "simple_tasks"],
                description="Fast Anthropic model for quick inference"
            ),
            
            # OpenAI Models (Fallback)
            "gpt-4o-mini": ModelConfig(
                name="gpt-4o-mini",
                provider=ModelProvider.OPENAI,
                tier=ModelTier.FALLBACK,
                cost_per_token=0.000001,  # Estimated
                max_tokens=128000,
                supports_function_calling=True
            ),
            "gpt-4o": ModelConfig(
                name="gpt-4o",
                provider=ModelProvider.OPENAI,
                tier=ModelTier.FALLBACK,
                cost_per_token=0.000030,  # Estimated
                max_tokens=128000,
                supports_function_calling=True
            )
        }
    
    def _create_default_agent_configs(self) -> dict[str, AgentModelConfig]:
        """Create default agent configurations with cost-optimized model selection"""
        return {
            "planner": AgentModelConfig(
                name="Content Planner",
                role="planner",
                primary_model="magistral-medium-latest",  # Reasoning model for complex planning
                fallback_model="claude-sonnet-4-0",       # Reasoning fallback
                provider="mistral",
                reasoning_required=True,                   # Requires reasoning capability
                tools=["research_query", "content_outline", "syllabus_analysis"],
                mcp_servers=["knowledge_bridge"],
                handoff_targets=["researcher", "writer"],
                instructions_template="You are an expert content planner specializing in educational material design..."
            ),
            
            "researcher": AgentModelConfig(
                name="Research Agent", 
                role="researcher",
                primary_model="mistral-small-latest",        # Fast model for research
                fallback_model="claude-3-5-haiku-latest",   # Fast Anthropic fallback
                provider="mistral",
                reasoning_required=False,                    # Fast inference preferred
                tools=["knowledge_search", "fact_check", "source_validation"],
                mcp_servers=["knowledge_bridge"],
                handoff_targets=["writer"],
                instructions_template="You are a thorough research agent focused on finding accurate information..."
            ),
            
            "writer": AgentModelConfig(
                name="Content Writer",
                role="writer", 
                primary_model="mistral-small-latest",        # Fast model for writing
                fallback_model="gpt-4o-mini",               # OpenAI fallback
                provider="mistral",
                reasoning_required=False,                    # Fast inference preferred
                tools=["content_generation", "style_guide", "markdown_formatting"],
                handoff_targets=["reviewer"],
                instructions_template="You are an expert content writer creating engaging educational materials..."
            ),
            
            "reviewer": AgentModelConfig(
                name="Content Reviewer",
                role="reviewer",
                primary_model="mistral-small-latest",        # Fast model for review
                fallback_model="claude-3-5-haiku-latest",   # Fast Anthropic fallback
                provider="mistral",
                reasoning_required=False,                    # Fast inference preferred
                tools=["quality_check", "style_validation"],
                handoff_targets=["evaluator"],
                instructions_template="You are a meticulous content reviewer ensuring quality and accuracy..."
            ),
            
            "evaluator": AgentModelConfig(
                name="Quality Evaluator",
                role="evaluator",
                primary_model="magistral-medium-latest",     # Reasoning model for evaluation
                fallback_model="claude-sonnet-4-0",         # Reasoning fallback
                provider="mistral",
                reasoning_required=True,                     # Requires reasoning capability
                tools=["quality_assessment", "bias_detection", "pedagogical_analysis"],
                instructions_template="You are an expert educational content evaluator with deep pedagogical knowledge..."
            ),
            
            "synthesizer": AgentModelConfig(
                name="Content Synthesizer",
                role="synthesizer",
                primary_model="magistral-medium-latest",     # Reasoning model for synthesis
                fallback_model="gpt-4o",                    # OpenAI fallback
                provider="mistral",
                reasoning_required=True,                     # Requires reasoning capability
                tools=["content_synthesis", "multi_source_integration"],
                instructions_template="You are a master content synthesizer combining multiple sources into coherent materials..."
            )
        }
    
    def _apply_env_overrides(self):
        """Apply environment variable overrides for model selection"""
        # Global model overrides
        if default_model := os.getenv("AGENT_MODEL_DEFAULT"):
            for agent_config in self._agent_configs.values():
                if agent_config.role not in ["planner", "evaluator"]:  # Keep thinking models
                    agent_config.primary_model = default_model
        
        # Specific role overrides
        role_overrides = {
            "planner": os.getenv("PLANNER_MODEL"),
            "evaluator": os.getenv("EVALUATOR_MODEL"),
            "researcher": os.getenv("RESEARCHER_MODEL"),
            "writer": os.getenv("WRITER_MODEL"),
            "reviewer": os.getenv("REVIEWER_MODEL"),
            "synthesizer": os.getenv("SYNTHESIZER_MODEL")
        }
        
        for role, model in role_overrides.items():
            if model and role in self._agent_configs:
                self._agent_configs[role].primary_model = model
                self.logger.info(f"Environment override: {role} using model {model}")
    
    def _load_config_file(self, config_path: str):
        """Load model and agent configurations from YAML file"""
        try:
            with open(config_path, encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            # Load model configurations
            if "models" in config_data:
                for model_name, model_data in config_data["models"].items():
                    provider_str = model_data.get("provider", "mistral")
                    tier_str = model_data.get("tier", "fast")
                    
                    # Convert string values to enums
                    try:
                        provider = ModelProvider(provider_str)
                        tier = ModelTier(tier_str)
                    except ValueError:
                        self.logger.warning(f"Invalid provider/tier for {model_name}, skipping")
                        continue
                    
                    self._model_configs[model_name] = ModelConfig(
                        name=model_name,
                        provider=provider,
                        tier=tier,
                        cost_per_token=model_data.get("cost_per_token", 0.0),
                        max_tokens=model_data.get("max_tokens", 4096),
                        supports_function_calling=model_data.get("function_calling", True),
                        reasoning_capable=model_data.get("reasoning", False),
                        use_cases=model_data.get("use_cases", []),
                        description=model_data.get("description", "")
                    )
            
            # Load agent configurations
            if "agents" in config_data:
                for role, agent_data in config_data["agents"].items():
                    if role in self._agent_configs:
                        # Update existing config
                        agent_config = self._agent_configs[role]
                        agent_config.primary_model = agent_data.get("primary_model", agent_config.primary_model)
                        agent_config.fallback_model = agent_data.get("fallback_model", agent_config.fallback_model)
                        agent_config.provider = agent_data.get("provider", agent_config.provider)
                        agent_config.reasoning_required = agent_data.get("reasoning_required", agent_config.reasoning_required)
                        agent_config.tools = agent_data.get("tools", agent_config.tools)
                        agent_config.mcp_servers = agent_data.get("mcp_servers", agent_config.mcp_servers)
                        agent_config.handoff_targets = agent_data.get("handoff_targets", agent_config.handoff_targets)
                    else:
                        # Create new config
                        self._agent_configs[role] = AgentModelConfig(
                            name=agent_data.get("name", f"{role.title()} Agent"),
                            role=role,
                            primary_model=agent_data.get("primary_model", "mistral-small-latest"),
                            fallback_model=agent_data.get("fallback_model"),
                            provider=agent_data.get("provider", "mistral"),
                            reasoning_required=agent_data.get("reasoning_required", False),
                            tools=agent_data.get("tools", []),
                            mcp_servers=agent_data.get("mcp_servers", []),
                            handoff_targets=agent_data.get("handoff_targets", [])
                        )
            
            self.logger.info(f"Loaded configuration from {config_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to load config file {config_path}: {e}")
    
    def get_model_for_agent(self, agent_role: str, use_fallback: bool = False) -> LitellmModel:
        """
        Get configured model for specific agent role.
        
        Args:
            agent_role: Role of the agent (planner, researcher, writer, etc.)
            use_fallback: Whether to use fallback model instead of primary
            
        Returns:
            Configured LitellmModel instance
        """
        if agent_role not in self._agent_configs:
            self.logger.warning(f"Unknown agent role: {agent_role}, using default researcher config")
            agent_role = "researcher"
        
        agent_config = self._agent_configs[agent_role]
        
        # Select model (primary or fallback)
        model_name = agent_config.fallback_model if use_fallback else agent_config.primary_model
        if not model_name:
            model_name = agent_config.primary_model  # Fallback to primary if no fallback defined
        
        # Get model configuration
        if model_name not in self._model_configs:
            self.logger.error(f"Model {model_name} not found in configurations")
            # Use mistral-small as ultimate fallback
            model_name = "mistral-small-latest"
        
        model_config = self._model_configs[model_name]
        
        # Get API key
        api_key = self._get_api_key(model_config.provider)
        if not api_key:
            self.logger.warning(f"No API key found for {model_config.provider.value}, trying fallback")
            return self._get_fallback_model(agent_role)
        
        # Create LiteLLM model
        model_path = f"{model_config.provider.value}/{model_name}"
        
        try:
            litellm_model = LitellmModel(
                model=model_path,
                api_key=api_key
            )
            
            self.logger.info(f"Created model for {agent_role}: {model_path}")
            return litellm_model
            
        except Exception as e:
            self.logger.error(f"Failed to create model {model_path}: {e}")
            return self._get_fallback_model(agent_role)
    
    def _get_api_key(self, provider: ModelProvider) -> str | None:
        """Get API key for specific provider"""
        key_map = {
            ModelProvider.MISTRAL: "MISTRAL_API_KEY",
            ModelProvider.ANTHROPIC: "ANTHROPIC_API_KEY", 
            ModelProvider.OPENAI: "OPENAI_API_KEY"
        }
        
        env_var = key_map.get(provider)
        if not env_var:
            return None
            
        return os.getenv(env_var)
    
    def _get_fallback_model(self, agent_role: str) -> LitellmModel:
        """Get fallback model when primary fails"""
        # Try OpenAI as ultimate fallback
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            try:
                fallback_model = LitellmModel(
                    model="openai/gpt-4o-mini",
                    api_key=openai_key
                )
                self.logger.warning(f"Using OpenAI fallback for {agent_role}")
                return fallback_model
            except Exception as e:
                self.logger.error(f"OpenAI fallback failed: {e}")
        
        # If all else fails, create a mock model that will raise appropriate errors
        raise RuntimeError(f"No available models for agent {agent_role}. Please check API keys.")
    
    def get_agent_config(self, agent_role: str) -> AgentModelConfig:
        """Get complete configuration for an agent role"""
        if agent_role not in self._agent_configs:
            self.logger.warning(f"Unknown agent role: {agent_role}")
            # Return default config
            return AgentModelConfig(
                name=f"{agent_role.title()} Agent",
                role=agent_role,
                primary_model="mistral-small-latest",
                provider="mistral"
            )
        
        return self._agent_configs[agent_role]
    
    def list_available_models(self) -> dict[str, dict[str, Any]]:
        """List all configured models with their capabilities"""
        return {
            name: {
                "provider": config.provider.value,
                "tier": config.tier.value,
                "cost_per_token": config.cost_per_token,
                "max_tokens": config.max_tokens,
                "supports_function_calling": config.supports_function_calling,
                "api_key_available": bool(self._get_api_key(config.provider))
            }
            for name, config in self._model_configs.items()
        }
    
    def get_cost_estimate(self, agent_role: str, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost for specific agent and token usage"""
        agent_config = self.get_agent_config(agent_role)
        model_config = self._model_configs.get(agent_config.primary_model)
        
        if not model_config:
            return 0.0
        
        total_tokens = input_tokens + output_tokens
        return total_tokens * model_config.cost_per_token
    
    def health_check(self) -> dict[str, Any]:
        """Check health status of all configured providers"""
        health_status = {
            "status": "healthy",
            "providers": {},
            "models_available": 0,
            "default_assignments": {}
        }
        
        # Check each provider
        for provider in ModelProvider:
            api_key = self._get_api_key(provider)
            provider_models = [
                name for name, config in self._model_configs.items()
                if config.provider == provider
            ]
            
            health_status["providers"][provider.value] = {
                "api_key_configured": bool(api_key),
                "models_count": len(provider_models),
                "models": provider_models
            }
            
            if api_key:
                health_status["models_available"] += len(provider_models)
        
        # Show default agent assignments
        for role, config in self._agent_configs.items():
            health_status["default_assignments"][role] = {
                "primary_model": config.primary_model,
                "fallback_model": config.fallback_model,
                "provider": config.provider
            }
        
        # Determine overall health
        if health_status["models_available"] == 0:
            health_status["status"] = "unhealthy"
        elif health_status["models_available"] < 3:
            health_status["status"] = "degraded"
        
        return health_status


# Convenience function for backward compatibility
def create_model_manager(config_path: str | None = None) -> MultiModelManager:
    """
    Create and configure MultiModelManager instance.
    
    Args:
        config_path: Optional path to YAML configuration file
        
    Returns:
        Configured MultiModelManager instance
    """
    return MultiModelManager(config_path)