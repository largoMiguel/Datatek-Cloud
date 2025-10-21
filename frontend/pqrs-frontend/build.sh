#!/usr/bin/env bash
# Script de build para Frontend en Render

set -o errexit  # Salir si hay error

echo "→ Instalando dependencias de Node..."
npm install

echo "→ Compilando Angular para producción..."
npm run build:prod

echo "→ Build del frontend completado exitosamente!"
