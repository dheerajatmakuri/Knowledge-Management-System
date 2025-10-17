"""Configuration management for the Knowledge Management System."""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Central configuration manager for the application."""
    
    _instance = None
    _config: Dict[str, Any] = {}
    
    def __new__(cls):
        """Singleton pattern to ensure only one config instance."""
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self) -> None:
        """Load configuration from YAML file and environment variables."""
        # Get project root
        project_root = Path(__file__).parent.parent
        config_file = project_root / "config" / "config.yaml"
        
        # Load YAML config
        if config_file.exists():
            with open(config_file, 'r') as f:
                self._config = yaml.safe_load(f)
        
        # Override with environment variables
        self._apply_env_overrides()
        
        # Create necessary directories
        self._create_directories()
    
    def _apply_env_overrides(self) -> None:
        """Override config values with environment variables."""
        env_mappings = {
            'OPENAI_API_KEY': ['assistant', 'llm', 'api_key'],
            'DATABASE_PATH': ['database', 'connection', 'path'],
            'EMBEDDINGS_MODEL': ['embeddings', 'model'],
            'LOG_LEVEL': ['logging', 'level'],
            'USE_LOCAL_MODEL': ['assistant', 'llm', 'use_local'],
        }
        
        for env_var, config_path in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # Navigate to the nested config location
                current = self._config
                for key in config_path[:-1]:
                    if key not in current:
                        current[key] = {}
                    current = current[key]
                
                # Convert boolean strings
                if value.lower() in ('true', 'false'):
                    value = value.lower() == 'true'
                
                current[config_path[-1]] = value
    
    def _create_directories(self) -> None:
        """Create necessary directories for the application."""
        project_root = Path(__file__).parent.parent
        
        directories = [
            'data',
            'data/embeddings',
            'data/cache',
            'data/backups',
            'logs',
        ]
        
        for directory in directories:
            path = project_root / directory
            path.mkdir(parents=True, exist_ok=True)
    
    def get(self, *keys: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.
        
        Args:
            *keys: Configuration keys (e.g., 'database', 'connection', 'path')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        current = self._config
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current
    
    def get_all(self) -> Dict[str, Any]:
        """Get the entire configuration dictionary."""
        return self._config.copy()
    
    @property
    def database_path(self) -> str:
        """Get database path."""
        return self.get('database', 'connection', 'path', default='data/database.db')
    
    @property
    def embeddings_model(self) -> str:
        """Get embeddings model name."""
        return self.get('embeddings', 'model', default='all-MiniLM-L6-v2')
    
    @property
    def openai_api_key(self) -> Optional[str]:
        """Get OpenAI API key."""
        return os.getenv('OPENAI_API_KEY') or self.get('assistant', 'llm', 'api_key')
    
    @property
    def use_local_model(self) -> bool:
        """Check if local model should be used."""
        return os.getenv('USE_LOCAL_MODEL', 'false').lower() == 'true'
    
    @property
    def log_level(self) -> str:
        """Get logging level."""
        return os.getenv('LOG_LEVEL', self.get('logging', 'level', default='INFO'))


# Global config instance
config = Config()


def get_config() -> Config:
    """Get the global configuration instance."""
    return config


__all__ = ['Config', 'config', 'get_config']
