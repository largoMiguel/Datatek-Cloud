#!/usr/bin/env bash
# Script de build para Render.com

set -o errexit  # Salir si hay error

echo "→ Instalando dependencias..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo "→ Build completado exitosamente!"
