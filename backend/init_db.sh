#!/usr/bin/env bash
# Script simplificado para validación de conexión DB

set -o errexit  # Salir si hay error

echo "→ Validando configuración de base de datos..."
python -c "from app.config.database import engine; engine.connect(); print('✓ Conexión a base de datos exitosa')"
echo "→ Validación completada"
