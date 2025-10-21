#!/usr/bin/env bash
# Script de build para Render.com

set -o errexit  # Salir si hay error

echo "→ Instalando dependencias..."
pip install --upgrade pip
pip install -r requirements.txt

echo "→ Inicializando base de datos..."
python -c "
from app.main import Base, engine
print('Creando tablas...')
Base.metadata.create_all(bind=engine)
print('✓ Tablas creadas exitosamente')
"

echo "→ Build completado exitosamente!"
