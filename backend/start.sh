#!/bin/bash

# Script para ejecutar el backend FastAPI

# Verificar si está en el directorio correcto
if [ ! -f "requirements.txt" ]; then
    echo "Error: Ejecuta este script desde el directorio backend/"
    exit 1
fi

# Crear entorno virtual si no existe
if [ ! -d "venv" ]; then
    echo "Creando entorno virtual..."
    python3 -m venv venv
fi

# Activar entorno virtual
echo "Activando entorno virtual..."
source venv/bin/activate

# Instalar dependencias
echo "Instalando dependencias..."
pip install -r requirements.txt

# Ejecutar la aplicación
echo "Iniciando servidor FastAPI..."
echo "Servidor disponible en: http://localhost:8000"
echo "Documentación API en: http://localhost:8000/docs"
echo ""
echo "Usuario administrador por defecto:"
echo "Usuario: admin"
echo "Contraseña: admin123"
echo ""
echo "Presiona Ctrl+C para detener el servidor"

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000