#!/bin/bash
# ============================================================================
# COMANDO DIRECTO - EJECUTAR MIGRACIÓN EN PRODUCCIÓN
# ============================================================================
#
# Este script ejecuta la migración completa en producción con un solo comando.
# Es el método más rápido y directo.
#
# Uso: ./EJECUTAR_MIGRACION_PRODUCCION.sh
#
# ============================================================================

set -e

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

clear

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                                    ║${NC}"
echo -e "${BLUE}║       MIGRACIÓN COMPLETA DE BASE DE DATOS - PRODUCCIÓN            ║${NC}"
echo -e "${BLUE}║                                                                    ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}Backend:${NC} https://pqrs-backend.onrender.com"
echo -e "${YELLOW}Clave:${NC}   tu-clave-secreta-2024"
echo ""
echo -e "${BLUE}────────────────────────────────────────────────────────────────────${NC}"
echo ""

# Confirmación
echo -e "${YELLOW}⚠️  CONFIRMACIÓN REQUERIDA${NC}"
echo ""
echo "Esta acción ejecutará la migración COMPLETA en la base de datos de producción."
echo "La migración es segura, idempotente y no elimina datos existentes."
echo ""
read -p "¿Deseas continuar? (s/N): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Ss]$ ]]; then
    echo -e "${RED}✗ Migración cancelada por el usuario${NC}"
    exit 0
fi

echo ""
echo -e "${BLUE}────────────────────────────────────────────────────────────────────${NC}"
echo ""
echo -e "${GREEN}✓ Iniciando migración...${NC}"
echo -e "${YELLOW}⏳ Esto puede tomar 30-60 segundos, por favor espera...${NC}"
echo ""

# Ejecutar migración
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
  https://pqrs-backend.onrender.com/api/migrations/run/status \
  -H "X-Migration-Key: tu-clave-secreta-2024" \
  -H "Content-Type: application/json")

# Separar código HTTP del body
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

echo ""
echo -e "${BLUE}────────────────────────────────────────────────────────────────────${NC}"
echo ""

# Verificar código HTTP
if [ "$HTTP_CODE" -eq 200 ]; then
    # Parsear JSON para verificar status
    STATUS=$(echo "$BODY" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status','unknown'))" 2>/dev/null || echo "unknown")
    
    if [ "$STATUS" = "success" ]; then
        echo -e "${GREEN}╔════════════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${GREEN}║                                                                    ║${NC}"
        echo -e "${GREEN}║                  ✓ MIGRACIÓN EXITOSA ✓                            ║${NC}"
        echo -e "${GREEN}║                                                                    ║${NC}"
        echo -e "${GREEN}╚════════════════════════════════════════════════════════════════════╝${NC}"
        echo ""
        
        # Mostrar estadísticas
        echo -e "${BLUE}📊 Estadísticas:${NC}"
        echo "$BODY" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f\"  • Total operaciones: {data.get('total_results', 0)}\")
    print(f\"  • Errores: {data.get('total_errors', 0)}\")
    print(f\"  • Timestamp: {data.get('timestamp', 'N/A')}\")
except:
    pass
" 2>/dev/null
        
        echo ""
        echo -e "${BLUE}📝 Últimos resultados:${NC}"
        echo "$BODY" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    results = data.get('results', [])
    for i, result in enumerate(results[-10:], 1):
        if '✓' in result:
            print(f\"  {i}. ✓ {result.replace('✓ ', '')}\")
        elif '⚠' in result:
            print(f\"  {i}. ⚠ {result.replace('⚠ ', '')}\")
        else:
            print(f\"  {i}. {result}\")
except:
    pass
" 2>/dev/null
        
        echo ""
        echo -e "${GREEN}✓ La base de datos ha sido migrada exitosamente${NC}"
        echo ""
        echo -e "${YELLOW}📌 Próximos pasos:${NC}"
        echo "  1. Verifica el frontend: https://pqrs-frontend.onrender.com"
        echo "  2. Prueba login y funcionalidades básicas"
        echo "  3. Revisa que todos los módulos carguen correctamente"
        echo ""
        
        # Verificar estado final
        echo -e "${BLUE}🔍 Verificando estado final...${NC}"
        FINAL_STATUS=$(curl -s https://pqrs-backend.onrender.com/api/migrations/status)
        echo "$FINAL_STATUS" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    stats = data.get('statistics', {})
    completeness = stats.get('completeness_percentage', 0)
    total_tables = stats.get('total_tables', 0)
    print(f\"  • Total de tablas: {total_tables}\")
    print(f\"  • Completitud: {completeness:.1f}%\")
    if completeness >= 100:
        print(\"  ✓ Base de datos completamente migrada\")
    else:
        print(f\"  ⚠ Algunas tablas pueden estar faltando ({completeness:.1f}%)\")
except:
    print(\"  ⚠ No se pudo verificar estado final\")
" 2>/dev/null
        
        echo ""
        echo -e "${GREEN}════════════════════════════════════════════════════════════════════${NC}"
        echo -e "${GREEN}                     ¡PROCESO COMPLETADO!                          ${NC}"
        echo -e "${GREEN}════════════════════════════════════════════════════════════════════${NC}"
        echo ""
        
    elif [ "$STATUS" = "already_running" ]; then
        echo -e "${YELLOW}⚠️  Ya hay una migración en ejecución${NC}"
        echo ""
        echo "Espera 2-3 minutos e intenta nuevamente, o verifica el estado:"
        echo "  curl https://pqrs-backend.onrender.com/api/migrations/status"
        echo ""
        exit 1
        
    elif [ "$STATUS" = "error" ]; then
        echo -e "${RED}╔════════════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${RED}║                                                                    ║${NC}"
        echo -e "${RED}║                  ✗ ERROR EN MIGRACIÓN ✗                           ║${NC}"
        echo -e "${RED}║                                                                    ║${NC}"
        echo -e "${RED}╚════════════════════════════════════════════════════════════════════╝${NC}"
        echo ""
        
        echo -e "${RED}❌ La migración falló. Detalles:${NC}"
        echo ""
        echo "$BODY" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f\"Mensaje: {data.get('message', 'Error desconocido')}\")
    print(\"\")
    errors = data.get('errors', [])
    if errors:
        print(\"Errores:\")
        for error in errors[:5]:
            print(f\"  • {error}\")
except:
    print(\"No se pudo parsear la respuesta\")
" 2>/dev/null
        
        echo ""
        echo -e "${YELLOW}📋 Respuesta completa guardada en migration_error.json${NC}"
        echo "$BODY" > migration_error.json
        echo ""
        exit 1
    else
        echo -e "${YELLOW}⚠️  Estado desconocido: $STATUS${NC}"
        echo ""
        echo "Respuesta completa:"
        echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
        echo ""
        exit 1
    fi
    
elif [ "$HTTP_CODE" -eq 403 ]; then
    echo -e "${RED}╔════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║                                                                    ║${NC}"
    echo -e "${RED}║                  ✗ ERROR DE AUTENTICACIÓN ✗                       ║${NC}"
    echo -e "${RED}║                                                                    ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${RED}❌ Clave de migración inválida${NC}"
    echo ""
    echo "Verifica que estés usando la clave correcta:"
    echo "  X-Migration-Key: tu-clave-secreta-2024"
    echo ""
    echo "Si el problema persiste, verifica la variable MIGRATION_SECRET_KEY en Render."
    echo ""
    exit 1
    
else
    echo -e "${RED}╔════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║                                                                    ║${NC}"
    echo -e "${RED}║                  ✗ ERROR HTTP $HTTP_CODE ✗                           ║${NC}"
    echo -e "${RED}║                                                                    ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Respuesta del servidor:"
    echo "$BODY"
    echo ""
    exit 1
fi

# Fin del script
exit 0
