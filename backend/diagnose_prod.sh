#!/bin/bash
# Script de diagnóstico para verificar el estado del backend en producción

set -e

BACKEND_URL="https://pqrs-backend.onrender.com"
FRONTEND_URL="https://pqrs-frontend.onrender.com"

echo ""
echo "🔍 ========================================="
echo "   DIAGNÓSTICO DEL BACKEND EN PRODUCCIÓN"
echo "========================================="
echo ""

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Health check
echo "1️⃣  Verificando health check..."
if curl -s -f "${BACKEND_URL}/health" > /dev/null; then
    echo -e "   ${GREEN}✅ Health check OK${NC}"
    curl -s "${BACKEND_URL}/health" | jq .
else
    echo -e "   ${RED}❌ Health check FAILED${NC}"
fi
echo ""

# Test 2: Endpoint de entidades
echo "2️⃣  Verificando endpoint de entidades..."
ENTITIES_RESPONSE=$(curl -s -w "\n%{http_code}" "${BACKEND_URL}/api/entities" | tail -n 1)
if [ "$ENTITIES_RESPONSE" = "200" ]; then
    echo -e "   ${GREEN}✅ Endpoint /api/entities responde (200)${NC}"
elif [ "$ENTITIES_RESPONSE" = "000" ]; then
    echo -e "   ${RED}❌ Endpoint /api/entities no responde (timeout)${NC}"
    echo -e "   ${YELLOW}⚠️  Posible problema: Base de datos no conectada${NC}"
else
    echo -e "   ${RED}❌ Endpoint /api/entities error (${ENTITIES_RESPONSE})${NC}"
fi
echo ""

# Test 3: CORS Preflight
echo "3️⃣  Verificando configuración CORS..."
CORS_RESPONSE=$(curl -s -I -X OPTIONS \
    -H "Origin: ${FRONTEND_URL}" \
    -H "Access-Control-Request-Method: GET" \
    -H "Access-Control-Request-Headers: authorization" \
    "${BACKEND_URL}/api/entities" | grep -i "access-control-allow-origin" || echo "NO_CORS")

if [ "$CORS_RESPONSE" != "NO_CORS" ]; then
    echo -e "   ${GREEN}✅ CORS configurado${NC}"
    echo "   $CORS_RESPONSE"
else
    echo -e "   ${RED}❌ CORS no configurado correctamente${NC}"
    echo -e "   ${YELLOW}⚠️  Verificar variable ALLOWED_ORIGINS en Render${NC}"
fi
echo ""

# Test 4: Endpoint de contratación (proxy SECOP II)
echo "4️⃣  Verificando endpoint de contratación..."
CONTRATACION_RESPONSE=$(curl -s -w "\n%{http_code}" \
    "${BACKEND_URL}/api/contratacion/proxy?nit_entidad=891801994&limit=1" | tail -n 1)
if [ "$CONTRATACION_RESPONSE" = "200" ]; then
    echo -e "   ${GREEN}✅ Endpoint /api/contratacion/proxy responde (200)${NC}"
else
    echo -e "   ${YELLOW}⚠️  Endpoint /api/contratacion/proxy (${CONTRATACION_RESPONSE})${NC}"
fi
echo ""

# Test 5: Auth endpoint
echo "5️⃣  Verificando endpoint de autenticación..."
AUTH_RESPONSE=$(curl -s -w "\n%{http_code}" \
    -X POST "${BACKEND_URL}/api/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"username":"test","password":"test"}' | tail -n 1)
if [ "$AUTH_RESPONSE" = "401" ] || [ "$AUTH_RESPONSE" = "422" ]; then
    echo -e "   ${GREEN}✅ Endpoint /api/auth/login responde (${AUTH_RESPONSE})${NC}"
    echo -e "   ${GREEN}   (401/422 es esperado sin credenciales válidas)${NC}"
elif [ "$AUTH_RESPONSE" = "000" ]; then
    echo -e "   ${RED}❌ Endpoint /api/auth/login no responde (timeout)${NC}"
else
    echo -e "   ${YELLOW}⚠️  Endpoint /api/auth/login (${AUTH_RESPONSE})${NC}"
fi
echo ""

# Resumen
echo "========================================="
echo "   RESUMEN DEL DIAGNÓSTICO"
echo "========================================="
echo ""
echo "Si ves errores (❌) o advertencias (⚠️), revisa:"
echo ""
echo "1. Variables de entorno en Render dashboard:"
echo "   - DATABASE_URL (debe apuntar a PostgreSQL de Render)"
echo "   - ALLOWED_ORIGINS (debe incluir ${FRONTEND_URL})"
echo "   - SECRET_KEY (para JWT)"
echo ""
echo "2. Estado de la base de datos PostgreSQL:"
echo "   - Debe estar 'Running' en Render"
echo "   - External URL debe ser accesible"
echo ""
echo "3. Logs del backend en Render:"
echo "   - Buscar mensajes de error con ❌"
echo "   - Verificar conexión a base de datos"
echo ""
echo "Para más información, ver:"
echo "📄 DIAGNOSTICO_ERROR_PRODUCCION.md"
echo ""
