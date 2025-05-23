
import os
from typing import Optional
from pydantic import BaseModel
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Configurações da aplicação."""
    
    # Database
    database_url: str = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:6000/postgres")
    
    # OpenAI
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    openai_embedding_model: str = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-large")
    
    # Chat settings
    max_history_messages: int = 10
    max_similar_messages: int = 3
    similarity_threshold: float = 0.3
    
    # API settings
    api_title: str = "Terabyte Challenge Chat API"
    api_description: str = "API de chat with LLM, vector search e function calling"
    api_version: str = "1.0.0"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

# Instância global das configurações
_settings: Optional[Settings] = None

def get_settings() -> Settings:
    """Retorna as configurações da aplicação (singleton)."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

# Para compatibilidade
settings = get_settings() 