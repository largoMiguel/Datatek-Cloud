#!/usr/bin/env bash
# Script para ejecutar migraciones en producción (Render)
# Uso: ./run_migration_prod.sh

set -e  # Salir si hay error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║         Script de Migraciones - PQRS Alcaldía        ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# URL del backend en producción
BACKEND_URL="${BACKEND_URL:-https://pqrs-backend.onrender.com}"

# Clave de migración (leer desde variable de entorno o solicitar)
if [ -z "$MIGRATION_KEY" ]; then
    echo -e "${YELLOW}⚠️  No se encontró MIGRATION_KEY en variables de entorno${NC}"
    echo -e "${YELLOW}Por favor ingresa la clave de migración:${NC}"
    read -s MIGRATION_KEY
    echo ""
fi

if [ -z "$MIGRATION_KEY" ]; then
    echo -e "${RED}❌ Error: Se requiere MIGRATION_KEY para ejecutar migraciones${NC}"
    exit 1
fi

echo -e "${YELLOW}🔍 Verificando estado de migraciones...${NC}"
echo ""

# Verificar estado actual
STATUS_RESPONSE=$(curl -s -X GET \
    -H "X-Migration-Key: $MIGRATION_KEY" \
    "$BACKEND_URL/api/migrations/status")

if echo "$STATUS_RESPONSE" | grep -q "detail"; then
    echo -e "${RED}❌ Error al verificar estado:${NC}"
    echo "$STATUS_RESPONSE" | jq '.'
    exit 1
fi

echo -e "${GREEN}✅ Estado actual:${NC}"
echo "$STATUS_RESPONSE" | jq '.'
echo ""

# Preguntar confirmación
echo -e "${YELLOW}¿Deseas ejecutar las migraciones? (si/no):${NC}"
read -r CONFIRM

if [ "$CONFIRM" != "si" ] && [ "$CONFIRM" != "SI" ] && [ "$CONFIRM" != "s" ]; then
    echo -e "${YELLOW}Operación cancelada por el usuario${NC}"
    exit 0
fi

echo ""
echo -e "${YELLOW}🚀 Ejecutando migraciones...${NC}"
echo ""

# Ejecutar migraciones
MIGRATION_RESPONSE=$(curl -s -X POST \
    -H "X-Migration-Key: $MIGRATION_KEY" \
    "$BACKEND_URL/api/migrations/run")

if echo "$MIGRATION_RESPONSE" | grep -q "detail"; then
    echo -e "${RED}❌ Error ejecutando migraciones:${NC}"
    echo "$MIGRATION_RESPONSE" | jq '.'
    exit 1
fi

echo -e "${GREEN}✅ Migraciones ejecutadas exitosamente:${NC}"
echo "$MIGRATION_RESPONSE" | jq '.'
echo ""

echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              ✅ Proceso completado                     ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
