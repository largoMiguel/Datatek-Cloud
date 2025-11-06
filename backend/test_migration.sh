#!/bin/bash

# Script de Prueba de Migración Local
# ====================================
# Este script prueba la migración en un entorno local antes de ejecutar en producción

set -e  # Salir si hay errores

echo "🧪 SCRIPT DE PRUEBA DE MIGRACIÓN LOCAL"
echo "======================================"
echo ""

# Colores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Variables
BACKEND_URL="http://localhost:8000"
MIGRATION_KEY="tu-clave-secreta-2024"

echo -e "${YELLOW}📋 Paso 1: Verificando que el servidor esté corriendo...${NC}"
if curl -s -o /dev/null -w "%{http_code}" "${BACKEND_URL}/health" | grep -q "200"; then
    echo -e "${GREEN}✓ Servidor corriendo correctamente${NC}"
else
    echo -e "${RED}❌ Error: El servidor no está corriendo en ${BACKEND_URL}${NC}"
    echo "Inicia el servidor con: uvicorn app.main:app --reload"
    exit 1
fi

echo ""
echo -e "${YELLOW}📋 Paso 2: Verificando estado actual de la base de datos...${NC}"
STATUS_RESPONSE=$(curl -s "${BACKEND_URL}/api/migrations/status")

if echo "$STATUS_RESPONSE" | grep -q '"status": "ok"'; then
    echo -e "${GREEN}✓ Conexión a base de datos exitosa${NC}"
    
    # Mostrar estadísticas
    TOTAL_TABLES=$(echo "$STATUS_RESPONSE" | grep -o '"total_tables": [0-9]*' | grep -o '[0-9]*')
    echo "  Total de tablas: $TOTAL_TABLES"
    
    EXPECTED_TABLES=$(echo "$STATUS_RESPONSE" | grep -o '"expected_tables": [0-9]*' | grep -o '[0-9]*')
    echo "  Tablas esperadas: $EXPECTED_TABLES"
    
    COMPLETENESS=$(echo "$STATUS_RESPONSE" | grep -o '"completeness_percentage": [0-9.]*' | grep -o '[0-9.]*')
    echo "  Completitud: ${COMPLETENESS}%"
else
    echo -e "${RED}❌ Error conectando a la base de datos${NC}"
    echo "$STATUS_RESPONSE" | head -20
    exit 1
fi

echo ""
echo -e "${YELLOW}📋 Paso 3: Ejecutando migración completa...${NC}"
echo "Esto puede tomar algunos segundos..."

MIGRATION_RESPONSE=$(curl -s -X POST \
    -H "X-Migration-Key: ${MIGRATION_KEY}" \
    -H "Content-Type: application/json" \
    "${BACKEND_URL}/api/migrations/run/status")

# Verificar resultado
if echo "$MIGRATION_RESPONSE" | grep -q '"status": "success"'; then
    echo -e "${GREEN}✓✓✓ MIGRACIÓN COMPLETADA EXITOSAMENTE ✓✓✓${NC}"
    echo ""
    
    # Mostrar resumen
    TOTAL_RESULTS=$(echo "$MIGRATION_RESPONSE" | grep -o '"total_results": [0-9]*' | grep -o '[0-9]*')
    TOTAL_ERRORS=$(echo "$MIGRATION_RESPONSE" | grep -o '"total_errors": [0-9]*' | grep -o '[0-9]*')
    
    echo "📊 Resumen:"
    echo "  - Total de operaciones: $TOTAL_RESULTS"
    echo "  - Errores encontrados: $TOTAL_ERRORS"
    
    # Mostrar algunos resultados
    echo ""
    echo "📝 Últimos resultados:"
    echo "$MIGRATION_RESPONSE" | grep -o '"results": \[.*\]' | sed 's/\\n/\n  /g' | head -20
    
elif echo "$MIGRATION_RESPONSE" | grep -q '"status": "already_running"'; then
    echo -e "${YELLOW}⚠ Ya hay una migración en ejecución${NC}"
    echo "Espera a que termine e intenta nuevamente"
    exit 1
else
    echo -e "${RED}❌ ERROR EN MIGRACIÓN${NC}"
    echo ""
    echo "Detalles del error:"
    echo "$MIGRATION_RESPONSE" | head -30
    exit 1
fi

echo ""
echo -e "${YELLOW}📋 Paso 4: Verificando estado final...${NC}"
FINAL_STATUS=$(curl -s "${BACKEND_URL}/api/migrations/status")

FINAL_TABLES=$(echo "$FINAL_STATUS" | grep -o '"total_tables": [0-9]*' | grep -o '[0-9]*')
FINAL_COMPLETENESS=$(echo "$FINAL_STATUS" | grep -o '"completeness_percentage": [0-9.]*' | grep -o '[0-9.]*')

echo "  Total de tablas: $FINAL_TABLES"
echo "  Completitud: ${FINAL_COMPLETENESS}%"

if [ "$FINAL_COMPLETENESS" == "100" ] || [ "$FINAL_COMPLETENESS" == "100.0" ]; then
    echo -e "${GREEN}✓ Base de datos completamente migrada${NC}"
else
    echo -e "${YELLOW}⚠ Algunas tablas pueden estar faltando (${FINAL_COMPLETENESS}%)${NC}"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}🎉 PRUEBA DE MIGRACIÓN COMPLETADA${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Próximos pasos:"
echo "1. Revisa los logs arriba para verificar que todo esté correcto"
echo "2. Si hay warnings, investiga pero generalmente son seguros"
echo "3. Para producción, usa la misma migración en Render:"
echo ""
echo "   curl -X POST https://pqrs-backend.onrender.com/api/migrations/run/status \\"
echo "        -H \"X-Migration-Key: ${MIGRATION_KEY}\""
echo ""
