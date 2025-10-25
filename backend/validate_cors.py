#!/usr/bin/env python3
"""
Script para validar la configuración CORS del backend
"""
import os
import sys

def validate_cors():
    """Valida que ALLOWED_ORIGINS esté correctamente configurado"""
    print("\n🔍 Validando configuración CORS...\n")
    
    # Importar settings
    try:
        from app.config.settings import settings
    except ImportError:
        print("❌ Error: No se pudo importar settings")
        print("   Asegúrate de estar en el directorio /backend")
        return False
    
    # Verificar ALLOWED_ORIGINS
    allowed_origins = settings.allowed_origins
    cors_origins = settings.cors_origins
    
    print(f"📋 ALLOWED_ORIGINS (env): {allowed_origins}")
    print(f"📋 CORS Origins (parsed): {cors_origins}\n")
    
    # Validaciones
    errors = []
    warnings = []
    
    # 1. Verificar que no esté vacío
    if not allowed_origins or allowed_origins.strip() == "":
        errors.append("ALLOWED_ORIGINS está vacío")
    
    # 2. Verificar formato de URLs
    for origin in cors_origins:
        if origin.endswith('/'):
            warnings.append(f"⚠️  '{origin}' termina con '/' - debería removerse")
        
        if not origin.startswith('http://') and not origin.startswith('https://'):
            errors.append(f"'{origin}' no empieza con http:// o https://")
        
        # Verificar espacios
        if ' ' in origin:
            errors.append(f"'{origin}' contiene espacios")
    
    # 3. Verificar que incluya el frontend de producción
    production_frontend = "https://pqrs-frontend.onrender.com"
    if settings.environment == "production" and production_frontend not in cors_origins:
        warnings.append(f"⚠️  En producción pero '{production_frontend}' no está en ALLOWED_ORIGINS")
    
    # Mostrar resultados
    print("=" * 60)
    if errors:
        print("❌ ERRORES ENCONTRADOS:")
        for error in errors:
            print(f"   • {error}")
        print()
    
    if warnings:
        print("⚠️  ADVERTENCIAS:")
        for warning in warnings:
            print(f"   • {warning}")
        print()
    
    if not errors and not warnings:
        print("✅ Configuración CORS correcta")
        print()
        print("URLs permitidas:")
        for origin in cors_origins:
            print(f"   ✓ {origin}")
    
    print("=" * 60)
    
    # Información adicional
    print("\n📚 Información adicional:")
    print(f"   Environment: {settings.environment}")
    print(f"   Debug: {settings.debug}")
    print(f"   Database: {settings.database_url[:30]}...")
    
    return len(errors) == 0

if __name__ == "__main__":
    # Agregar el directorio backend al path
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, backend_dir)
    
    success = validate_cors()
    sys.exit(0 if success else 1)
