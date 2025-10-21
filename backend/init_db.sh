#!/usr/bin/env bash
# Script para inicializar la base de datos en Render
# Este script se ejecutará después del build

set -o errexit  # Salir si hay error

echo "→ Inicializando base de datos..."

# Ejecutar un comando Python para crear las tablas
python << END
from app.main import Base, engine
print("Creando tablas en la base de datos...")
Base.metadata.create_all(bind=engine)
print("✓ Tablas creadas exitosamente")
END

echo "→ Inicialización completada"
