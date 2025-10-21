#!/bin/bash

# Script para actualizar el backend en EC2
# Uso: ./scripts/update-backend.sh <IP-EC2> <PATH-TO-PEM-KEY>

set -e  # Salir si hay error

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Verificar argumentos
if [ "$#" -ne 2 ]; then
    echo -e "${RED}Error: Se requieren 2 argumentos${NC}"
    echo "Uso: $0 <IP-EC2> <PATH-TO-PEM-KEY>"
    echo "Ejemplo: $0 54.123.45.67 ~/Downloads/pqrs-backend-key.pem"
    exit 1
fi

EC2_IP=$1
PEM_KEY=$2

echo -e "${YELLOW}═══════════════════════════════════════════${NC}"
echo -e "${YELLOW}  Actualizando Backend en EC2${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════${NC}"

# Verificar que el archivo PEM existe
if [ ! -f "$PEM_KEY" ]; then
    echo -e "${RED}Error: El archivo PEM no existe: $PEM_KEY${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Archivo PEM encontrado${NC}"

# Verificar permisos del archivo PEM
chmod 400 "$PEM_KEY"

echo -e "${YELLOW}→ Conectando a EC2...${NC}"

# Comandos a ejecutar en EC2
ssh -i "$PEM_KEY" -o StrictHostKeyChecking=no ubuntu@"$EC2_IP" << 'ENDSSH'
    set -e
    
    echo "→ Navegando al directorio del proyecto..."
    cd /home/ubuntu/pqrs-app
    
    echo "→ Descargando últimos cambios..."
    git pull origin master
    
    echo "→ Activando entorno virtual..."
    cd backend
    source venv/bin/activate
    
    echo "→ Instalando/actualizando dependencias..."
    pip install -r requirements.txt
    
    echo "→ Reiniciando servicio..."
    sudo systemctl restart pqrs-backend
    
    echo "→ Verificando estado del servicio..."
    sleep 2
    sudo systemctl status pqrs-backend --no-pager -l
    
    echo ""
    echo "→ Probando endpoint de salud..."
    curl -s http://localhost:8000/health || echo "Error al conectar"
ENDSSH

echo -e "${GREEN}═══════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✓ Backend actualizado exitosamente${NC}"
echo -e "${GREEN}═══════════════════════════════════════════${NC}"
echo ""
echo -e "Puedes verificar en: ${YELLOW}http://$EC2_IP:8000/docs${NC}"
