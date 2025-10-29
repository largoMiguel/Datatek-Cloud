# Archivo para hacer que sea un paquete Python
from app.routes import auth, pqrs, users, planes, entities, migrations

__all__ = ["auth", "pqrs", "users", "planes", "entities", "migrations"]