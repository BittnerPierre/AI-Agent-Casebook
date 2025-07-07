"""Configuration management for agentic-research."""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

# Load environment variables from .env file
try:
    from dotenv import load_dotenv, find_dotenv
    load_dotenv(find_dotenv())
except ImportError:
    pass  # python-dotenv not available, skip loading


class VectorStoreConfig(BaseModel):
    """Configuration for vector store."""
    name: str = Field(default="Agentic Research Vector Store")
    description: str = Field(default="Vector store for research")
    expires_after_days: int = Field(default=30)
    vector_store_id: str = Field(default="")


class DataConfig(BaseModel):
    """Configuration for data sources."""
    urls_file: str = Field(default="urls.txt")
    knowledge_db_path: str = Field(default="data/knowledge_db.json")
    local_storage_dir: str = Field(default="data/")


class DebugConfig(BaseModel):
    """Configuration for debug mode."""
    enabled: bool = Field(default=False)
    output_dir: str = Field(default="debug_output")
    save_reports: bool = Field(default=True)


class LoggingConfig(BaseModel):
    """Configuration for logging."""
    level: str = Field(default="INFO")
    format: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


class ModelsConfig(BaseModel):
    """Configuration for OpenAI."""
    research_model: str = Field(default="litellm/anthropic/claude-3-7-sonnet-latest")
    planning_model: str = Field(default="litellm/anthropic/claude-3-7-sonnet-latest")
    search_model: str = Field(default="openai/gpt-4o-mini")
    writer_model: str = Field(default="litellm/anthropic/claude-3-7-sonnet-latest")
    reasoning_model: str = Field(default="openai/o3-mini")

class ManagerConfig(BaseModel):
    """Configuration for manager selection."""
    default_manager: str = Field(default="agentic_manager")


class Config(BaseModel):
    """Main configuration class."""
    vector_store: VectorStoreConfig
    data: DataConfig = Field(default_factory=DataConfig)
    debug: DebugConfig = Field(default_factory=DebugConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    models: ModelsConfig = Field(default_factory=ModelsConfig)
    manager: ManagerConfig = Field(default_factory=ManagerConfig)


class ConfigManager:
    """Manages configuration loading with environment variable override."""
    
    def __init__(self, config_path: Optional[Path] = None):
        if config_path is None:
            # Par défaut, chercher config.yaml dans le dossier du projet
            project_root = Path(__file__).parent.parent
            config_path = project_root / "config.yaml"
        
        self.config_path = config_path
        self._config: Optional[Config] = None
    
    def load_config(self) -> Config:
        """Load configuration from YAML file with environment variable overrides."""
        if self._config is not None:
            return self._config
        
        # Charger la configuration depuis le fichier YAML
        config_data = self._load_yaml_config()
        
        # Permettre l'override via les variables d'environnement
        config_data = self._apply_env_overrides(config_data)
        
        # Valider et créer l'objet de configuration
        self._config = Config(**config_data)
        return self._config
    
    def _load_yaml_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _apply_env_overrides(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment variable overrides to configuration."""
        # # Permettre l'override du vector store name via la variable d'environnement
        # vector_store_name = os.getenv("VECTOR_STORE_NAME")
        # if vector_store_name:
        #     if "vector_store" not in config_data:
        #         config_data["vector_store"] = {}
        #     config_data["vector_store"]["name"] = vector_store_name
        
        # Override du mode debug via variable d'environnement
        debug_enabled = os.getenv("DEBUG")
        if debug_enabled:
            if "debug" not in config_data:
                config_data["debug"] = {}
            config_data["debug"]["enabled"] = debug_enabled.lower() in ("true", "1", "yes", "on")
        
        # Override du manager par défaut via variable d'environnement
        default_manager = os.getenv("DEFAULT_MANAGER")
        if default_manager:
            if "manager" not in config_data:
                config_data["manager"] = {}
            config_data["manager"]["default_manager"] = default_manager
        
        return config_data
    
    @property
    def config(self) -> Config:
        """Get the loaded configuration."""
        if self._config is None:
            return self.load_config()
        return self._config


# Instance globale pour l'accès facile
config_manager = ConfigManager()


def get_config() -> Config:
    """Get the global configuration instance."""
    return config_manager.config


def get_vector_store_name() -> str:
    """Get the vector store ID from configuration."""
    return get_config().vector_store.name