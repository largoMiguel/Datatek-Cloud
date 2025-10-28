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
    
    # CORS - Múltiples orígenes separados por coma
    allowed_origins: str = "http://localhost:4200,https://pqrs-frontend.onrender.com"

    # Superadmin (para seed/control inicial)
    superadmin_username: str = "superadmin"
    superadmin_email: str = "superadmin@sistema.gov.co"
    superadmin_password: str = "changeMe!SuperSecure"
    
    # Mantenimiento/control (confirmación para operaciones peligrosas)
    maintenance_confirm_phrase: str = "CONFIRM_RESET"
    # Token opcional para reforzar seguridad de endpoints de mantenimiento (dejar vacío si no se usa)
    maintenance_token: str = ""
    
    @property
    def cors_origins(self) -> List[str]:
        """Convierte la cadena de orígenes permitidos en una lista"""
        origins = [origin.strip() for origin in self.allowed_origins.split(",")]
        # Agregar automáticamente variantes comunes si estamos en producción
        production_origins = []
        for origin in origins:
            if "onrender.com" in origin:
                production_origins.append(origin)
                # Agregar versión sin www si no está
                if origin.startswith("https://www."):
                    production_origins.append(origin.replace("https://www.", "https://"))
                elif origin.startswith("https://") and "www." not in origin:
                    production_origins.append(origin.replace("https://", "https://www."))
        return list(set(origins + production_origins))  # Eliminar duplicados
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignorar campos extra

settings = Settings()