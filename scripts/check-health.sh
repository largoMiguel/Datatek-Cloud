#!/bin/bash

# Script para verificar el estado de la aplicación desplegada
# Uso: ./scripts/check-health.sh <EC2-IP> [FRONTEND-URL]

set -e

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

if [ "$#" -lt 1 ]; then
    echo -e "${RED}Error: Se requiere la IP de EC2${NC}"
    echo "Uso: $0 <EC2-IP> [FRONTEND-URL]"
    exit 1
fi

EC2_IP=$1
FRONTEND_URL=${2:-""}

echo -e "${YELLOW}═══════════════════════════════════════════${NC}"
echo -e "${YELLOW}  Verificación de Salud del Sistema${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════${NC}"
echo ""

# Verificar Backend
echo -e "${YELLOW}→ Verificando Backend (EC2)...${NC}"
BACKEND_URL="http://$EC2_IP:8000"

if curl -s --connect-timeout 5 "$BACKEND_URL/health" > /dev/null; then
    echo -e "${GREEN}✓ Backend está funcionando${NC}"
    echo -e "  URL: $BACKEND_URL"
    echo -e "  Docs: $BACKEND_URL/docs"
else
    echo -e "${RED}✗ Backend no responde${NC}"
fi

echo ""

# Verificar Frontend si se proporcionó URL
if [ -n "$FRONTEND_URL" ]; then
    echo -e "${YELLOW}→ Verificando Frontend (S3)...${NC}"
    
    if curl -s --connect-timeout 5 "$FRONTEND_URL" > /dev/null; then
        echo -e "${GREEN}✓ Frontend está accesible${NC}"
        echo -e "  URL: $FRONTEND_URL"
    else
        echo -e "${RED}✗ Frontend no responde${NC}"
    fi
    echo ""
fi

# Verificar RDS (desde EC2)
echo -e "${YELLOW}→ Para verificar RDS, conéctate a EC2 y ejecuta:${NC}"
echo -e "  ssh ubuntu@$EC2_IP"
echo -e "  psql -h <RDS-ENDPOINT> -U pqrsadmin -d pqrs_db"

echo ""
echo -e "${GREEN}═══════════════════════════════════════════${NC}"
echo -e "${GREEN}  Verificación Completa${NC}"
echo -e "${GREEN}═══════════════════════════════════════════${NC}"
