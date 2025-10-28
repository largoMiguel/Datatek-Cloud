# Archivo para hacer que sea un paquete Python
from app.routes import auth, pqrs, users, planes, entities, maintenance

__all__ = ["auth", "pqrs", "users", "planes", "entities", "maintenance"]