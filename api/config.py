import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    """Configurações da aplicação."""
    
    # Database
    database_url: str = os.getenv("OPENAI_API_KEY")
    
    # OpenAI
    openai_api_key: str = os.getenv("OPENAI_MODEL")
    openai_model: str = os.getenv("OPENAI_MODEL")
    openai_embedding_model: str = os.getenv("OPENAI_EMBEDDING_MODEL")
    
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

# Instância global das configurações
settings = Settings()

def get_settings() -> Settings:
    """Retorna as configurações da aplicação."""
    return settings