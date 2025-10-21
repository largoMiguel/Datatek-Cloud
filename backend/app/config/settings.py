import os
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./pqrs_alcaldia.db"
    
    # JWT
    secret_key: str = "tu-clave-secreta-super-segura-cambiar-en-produccion"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # OpenAI
    openai_api_key: str = ""
    
    # Environment
    environment: str = "development"
    debug: bool = True
    
    # CORS
    allowed_origins: str = "http://localhost:4200"
    
    @property
    def cors_origins(self) -> List[str]:
        """Convierte la cadena de orígenes permitidos en una lista"""
        return [origin.strip() for origin in self.allowed_origins.split(",")]
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignorar campos extra

settings = Settings()