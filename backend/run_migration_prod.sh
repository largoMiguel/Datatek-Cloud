#!/usr/bin/env bash
# Script para ejecutar migraciones en producción via API

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Script de Migraciones - Producción ===${NC}\n"

# Verificar que se proporcione el token
if [ -z "$1" ]; then
    echo -e "${RED}Error: Debes proporcionar el token de autenticación${NC}"
    echo "Uso: ./run_migration_prod.sh YOUR_SUPERADMIN_TOKEN [API_URL]"
    echo ""
    echo "Ejemplo:"
    echo "  ./run_migration_prod.sh eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    echo "  ./run_migration_prod.sh YOUR_TOKEN https://tu-api.onrender.com"
    exit 1
fi

TOKEN=$1
API_URL=${2:-"https://pqrs-alcaldia-backend.onrender.com"}

echo -e "${YELLOW}API URL:${NC} $API_URL"
echo ""

# 1. Verificar estado actual
echo -e "${YELLOW}1. Verificando estado de la base de datos...${NC}"
STATUS_RESPONSE=$(curl -s "$API_URL/api/migrations/status")
echo "$STATUS_RESPONSE" | python -m json.tool 2>/dev/null || echo "$STATUS_RESPONSE"
echo ""

# 2. Ejecutar migraciones
echo -e "${YELLOW}2. Ejecutando migraciones...${NC}"
MIGRATION_RESPONSE=$(curl -s -X POST "$API_URL/api/migrations/run" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json")

echo "$MIGRATION_RESPONSE" | python -m json.tool 2>/dev/null || echo "$MIGRATION_RESPONSE"
echo ""

# 3. Verificar resultado
if echo "$MIGRATION_RESPONSE" | grep -q '"status": "success"'; then
    echo -e "${GREEN}✓ Migraciones completadas exitosamente${NC}"
else
    echo -e "${RED}✗ Error en las migraciones${NC}"
    exit 1
fi

# 4. Verificar estado final
echo -e "${YELLOW}3. Verificando estado final...${NC}"
FINAL_STATUS=$(curl -s "$API_URL/api/migrations/status")
echo "$FINAL_STATUS" | python -m json.tool 2>/dev/null || echo "$FINAL_STATUS"

echo ""
echo -e "${GREEN}=== Proceso completado ===${NC}"
