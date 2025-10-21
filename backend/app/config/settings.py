import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "sqlite:///./pqrs_alcaldia.db"
    secret_key: str = "tu-clave-secreta-super-segura-cambiar-en-produccion"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignorar campos extra

settings = Settings()