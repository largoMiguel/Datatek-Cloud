#!/usr/bin/env bash
# Script de build para Render.com

set -o errexit  # Salir si hay error

echo "→ Instalando dependencias..."
pip install --upgrade pip
pip install -r requirements.txt

echo "→ Build completado exitosamente!"
