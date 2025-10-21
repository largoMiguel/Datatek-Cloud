#!/bin/bash

# Script para desplegar el frontend en S3
# Uso: ./scripts/deploy-frontend.sh <BUCKET-NAME> [API-URL]

set -e  # Salir si hay error

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Verificar argumentos
if [ "$#" -lt 1 ]; then
    echo -e "${RED}Error: Se requiere al menos 1 argumento${NC}"
    echo "Uso: $0 <BUCKET-NAME> [API-URL]"
    echo "Ejemplo: $0 pqrs-alcaldia-frontend http://54.123.45.67:8000/api"
    exit 1
fi

BUCKET_NAME=$1
API_URL=${2:-""}

echo -e "${YELLOW}═══════════════════════════════════════════${NC}"
echo -e "${YELLOW}  Desplegando Frontend en S3${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════${NC}"

# Verificar que AWS CLI está instalado
if ! command -v aws &> /dev/null; then
    echo -e "${RED}Error: AWS CLI no está instalado${NC}"
    echo "Instala con: brew install awscli"
    exit 1
fi

echo -e "${GREEN}✓ AWS CLI encontrado${NC}"

# Verificar que estamos en el directorio correcto
if [ ! -f "frontend/pqrs-frontend/package.json" ]; then
    echo -e "${RED}Error: Debe ejecutar este script desde el directorio raíz del proyecto${NC}"
    exit 1
fi

# Si se proporcionó API_URL, actualizar environment.prod.ts
if [ -n "$API_URL" ]; then
    echo -e "${YELLOW}→ Actualizando API URL en environment.prod.ts...${NC}"
    cat > frontend/pqrs-frontend/src/environments/environment.prod.ts << EOF
export const environment = {
  production: true,
  apiUrl: '$API_URL',
  openaiApiKey: ''
};
EOF
    echo -e "${GREEN}✓ API URL actualizada a: $API_URL${NC}"
fi

echo -e "${YELLOW}→ Instalando dependencias...${NC}"
cd frontend/pqrs-frontend
npm install

echo -e "${YELLOW}→ Compilando para producción...${NC}"
npm run build:prod

echo -e "${GREEN}✓ Compilación exitosa${NC}"

# Verificar que el directorio de build existe
if [ ! -d "dist/pqrs-frontend/browser" ]; then
    echo -e "${RED}Error: Directorio de build no encontrado${NC}"
    exit 1
fi

echo -e "${YELLOW}→ Subiendo archivos a S3 bucket: $BUCKET_NAME...${NC}"
aws s3 sync dist/pqrs-frontend/browser/ s3://"$BUCKET_NAME"/ --delete

echo -e "${GREEN}✓ Archivos subidos correctamente${NC}"

# Obtener URL del bucket
BUCKET_URL="http://$BUCKET_NAME.s3-website-$(aws configure get region).amazonaws.com"

echo -e "${GREEN}═══════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✓ Frontend desplegado exitosamente${NC}"
echo -e "${GREEN}═══════════════════════════════════════════${NC}"
echo ""
echo -e "URL del sitio: ${BLUE}$BUCKET_URL${NC}"
echo ""
echo -e "${YELLOW}Nota:${NC} Si usas CloudFront, invalida el caché con:"
echo -e "${BLUE}aws cloudfront create-invalidation --distribution-id YOUR_DIST_ID --paths \"/*\"${NC}"
