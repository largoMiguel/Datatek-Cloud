#!/bin/bash

# Script para ejecutar el backend FastAPI

# Verificar si está en el directorio correcto
if [ ! -f "requirements.txt" ]; then
    echo "Error: Ejecuta este script desde el directorio backend/"
    exit 1
fi

# Resolver intérprete de Python (preferir 3.11)
if command -v python3.11 >/dev/null 2>&1; then
    PY=python3.11
elif [ -x "/Users/largo/.pyenv/versions/3.11.9/bin/python" ]; then
    PY="/Users/largo/.pyenv/versions/3.11.9/bin/python"
else
    PY=python3
fi

# Crear entorno virtual si no existe
if [ ! -d "venv" ]; then
        echo "Creando entorno virtual con $PY ..."
        "$PY" -m venv venv
fi

# Activar entorno virtual
echo "Activando entorno virtual..."
source venv/bin/activate

# Instalar dependencias
echo "Instalando dependencias..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

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