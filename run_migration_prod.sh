#!/bin/bash
# Script para ejecutar migración COMPLETA en producción
# Uso: ./run_migration_prod.sh [BACKEND_URL] [MIGRATION_KEY]

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

BACKEND_URL=${1:-"https://pqrs-backend.onrender.com"}
MIGRATION_KEY=${2:-"tu-clave-secreta-2024"}

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Migración COMPLETA de Base de Datos - Producción${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

echo -e "${YELLOW}📡 Backend URL: ${BACKEND_URL}${NC}"
echo -e "${YELLOW}🔑 Migration Key: ${MIGRATION_KEY:0:5}...${NC}\n"

# Función para hacer requests
function api_call() {
    local method=$1
    local endpoint=$2
    local extra_args="${3:-}"
    
    curl -s -X "$method" "${BACKEND_URL}${endpoint}" \
        -H "Content-Type: application/json" \
        $extra_args
}

# 1. Verificar estado actual
echo -e "${BLUE}📊 Paso 1: Verificando estado actual...${NC}"
STATUS_RESPONSE=$(api_call GET "/api/migrations/status")

echo "$STATUS_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$STATUS_RESPONSE"

# Mostrar estadísticas
echo "$STATUS_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    stats = data.get('statistics', {})
    print(f\"  Total tablas: {stats.get('total_tables', 0)}\")
    print(f\"  Completitud: {stats.get('completeness_percentage', 0):.1f}%\")
except:
    pass
" 2>/dev/null

# 2. Confirmar ejecución
echo -e "\n${BLUE}⚠️  CONFIRMACIÓN REQUERIDA${NC}"
echo -e "${YELLOW}Esto ejecutará la migración COMPLETA en producción.${NC}"
echo -e "${YELLOW}La migración es idempotente y segura.${NC}"
echo -e "\n${YELLOW}¿Continuar con la migración? (s/N)${NC}"
read -r confirm

if [[ ! "$confirm" =~ ^[sS]$ ]]; then
    echo -e "${GREEN}✓ Operación cancelada${NC}"
    exit 0
fi

# 3. Ejecutar migración completa
echo -e "\n${BLUE}🚀 Paso 2: Ejecutando migración completa...${NC}"
echo -e "${YELLOW}⏳ Esto puede tomar 30-60 segundos...${NC}\n"
MIGRATION_RESPONSE=$(api_call POST "/api/migrations/run/status" "-H \"X-Migration-Key: ${MIGRATION_KEY}\"")

echo "$MIGRATION_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$MIGRATION_RESPONSE"

# 4. Verificar resultado
if echo "$MIGRATION_RESPONSE" | grep -q '"status": "success"'; then
    echo -e "\n${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}✓✓✓ MIGRACIÓN EXITOSA ✓✓✓${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
    
    # Mostrar resultados
    echo -e "${BLUE}📝 Resultados:${NC}"
    echo "$MIGRATION_RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for result in data.get('results', []):
    print(f'  • {result}')
" 2>/dev/null || echo "  (ver respuesta completa arriba)"
    
    # Verificar estado final
    echo -e "\n${BLUE}📊 Paso 3: Verificando estado final...${NC}"
    FINAL_STATUS=$(api_call GET "/api/migrations/status")
    
    echo "$FINAL_STATUS" | python3 -c "
import sys, json
data = json.load(sys.stdin)
tables = data.get('critical_tables', {})
print('\n  Tablas críticas:')
for table, exists in tables.items():
    status = '✓' if exists else '✗'
    print(f'    {status} {table}')
" 2>/dev/null || echo "  (ver respuesta completa arriba)"
    
    echo -e "\n${GREEN}✓ Migración completada exitosamente${NC}"
    echo -e "${YELLOW}📌 Próximos pasos:${NC}"
    echo -e "  1. Verifica el frontend: https://pqrs-frontend.onrender.com"
    echo -e "  2. Prueba cada módulo (PQRS, Planes, PDM)"
    echo -e "  3. Revisa los logs si hay warnings"
    
elif echo "$MIGRATION_RESPONSE" | grep -q '"status": "error"'; then
    echo -e "\n${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}✗✗✗ ERROR EN LA MIGRACIÓN ✗✗✗${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
    
    echo -e "${RED}❌ La migración falló. Detalles arriba.${NC}"
    echo -e "${YELLOW}📌 Acciones recomendadas:${NC}"
    echo -e "  1. Revisa los logs del servidor backend"
    echo -e "  2. Verifica el estado de la base de datos"
    echo -e "  3. Si es necesario, restaura desde el backup"
    exit 1
else
    echo -e "\n${YELLOW}⚠️  Respuesta inesperada del servidor${NC}"
    echo -e "${YELLOW}Revisa la respuesta completa arriba${NC}"
    exit 1
fi

echo ""
