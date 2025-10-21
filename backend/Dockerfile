# Usar imagen oficial de Python
FROM python:3.11-slim

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias para psycopg2
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de dependencias
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación
COPY . .

# Exponer el puerto (Render usa PORT variable de entorno)
EXPOSE 8000

# Comando para ejecutar la aplicación con gunicorn
CMD gunicorn -k uvicorn.workers.UvicornWorker -w 4 -b 0.0.0.0:${PORT:-8000} app.main:app --timeout 120
