#!/usr/bin/env python3
"""Script para verificar la configuración del entorno en Render"""
import sys
sys.path.insert(0, '.')

from app.config.settings import settings

print("\n🔍 Configuración del entorno:")
print(f"   Environment: {settings.environment}")
print(f"   Debug: {settings.debug}")
print(f"   Database URL: {settings.database_url[:50]}...")
print(f"   ALLOWED_ORIGINS (raw): {settings.allowed_origins}")
print(f"   CORS Origins (parsed): {settings.cors_origins}")
print(f"   Migration Secret Key: {settings.migration_secret_key[:20]}...")
print("\n✅ Configuración cargada correctamente")
