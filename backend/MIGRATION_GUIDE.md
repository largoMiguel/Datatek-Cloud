# Guía de Migraciones - Módulo de Contratación

## 📋 Resumen

El módulo de Contratación **NO requiere cambios en la base de datos**. Todos los datos se obtienen en tiempo real desde la API pública SECOP II de Colombia.

## 🔧 Cambios Realizados

### Frontend (`pqrs-frontend`)
- ✅ Componente de Contratación con integración SECOP II
- ✅ Tabla profesional con filtros por columna
- ✅ KPIs interactivos con detalles
- ✅ Gráficas de análisis (estados, modalidades, timeline, proveedores, tipos)
- ✅ Alertas de contratos vencidos
- ✅ Navegación mejorada con barra global
- ✅ Diseño responsive y profesional

### Backend (`pqrs-backend`)
- ✅ Endpoint proxy para SECOP II (`/api/contratacion/proxy`)
- ✅ Endpoint de migraciones (`/api/migrations/run`, `/api/migrations/status`)
- ✅ Configuración de CORS para múltiples dominios

## 🚀 Deployment a Producción

### 1. Backend (Render)

El backend se despliega automáticamente al hacer push a GitHub.

**Variables de entorno requeridas en Render:**
```bash
# En Render Dashboard > Backend Service > Environment
MIGRATION_SECRET_KEY=tu-clave-secreta-super-segura-2024
DATABASE_URL=postgresql://...
SECRET_KEY=tu-jwt-secret-key
ALLOWED_ORIGINS=https://pqrs-frontend.onrender.com,http://localhost:4200
```

### 2. Frontend (Render/Netlify)

El frontend también se despliega automáticamente.

**Build Settings:**
```bash
Build Command: npm run build:prod
Publish Directory: dist/pqrs-frontend/browser
```

## 🔄 Ejecutar Migraciones en Producción

### Opción 1: Script Automático (Recomendado)

```bash
cd backend
export MIGRATION_KEY="tu-clave-secreta-super-segura-2024"
./run_migration_prod.sh
```

### Opción 2: Curl Directo

**1. Verificar estado:**
```bash
curl -X GET \
  https://pqrs-backend-mvcp.onrender.com/api/migrations/status \
  -H "X-Migration-Key: tu-clave-secreta-super-segura-2024" \
  | jq '.'
```

**2. Ejecutar migraciones:**
```bash
curl -X POST \
  https://pqrs-backend-mvcp.onrender.com/api/migrations/run \
  -H "X-Migration-Key: tu-clave-secreta-super-segura-2024" \
  | jq '.'
```

### Opción 3: Desde la UI de Render

1. Ve a Render Dashboard > Backend Service
2. Abre la Shell
3. Ejecuta:
```bash
python -c "
import os
os.environ['MIGRATION_SECRET_KEY'] = 'tu-clave-secreta'
import requests
response = requests.post(
    'http://localhost:10000/api/migrations/run',
    headers={'X-Migration-Key': os.environ['MIGRATION_SECRET_KEY']}
)
print(response.json())
"
```

## ✅ Verificación Post-Deployment

### 1. Backend
```bash
# Health check
curl https://pqrs-backend-mvcp.onrender.com/health

# Verificar endpoint de contratación
curl "https://pqrs-backend-mvcp.onrender.com/api/contratacion/proxy?nit_entidad=891801994&limit=10"
```

### 2. Frontend
1. Acceder a: https://pqrs-frontend.onrender.com
2. Login con superadmin
3. Ir a Dashboard > Contratación
4. Verificar que carga datos de SECOP II
5. Probar filtros por columna
6. Verificar alertas de contratos vencidos

## 📊 Endpoints del Módulo de Contratación

### Backend Proxy
```
GET /api/contratacion/proxy
```

**Query Parameters:**
- `nit_entidad`: NIT de la entidad (requerido)
- `limit`: Límite de resultados (default: 1000)
- `offset`: Desplazamiento para paginación (default: 0)
- `fecha_desde`: Fecha desde (YYYY-MM-DD)
- `fecha_hasta`: Fecha hasta (YYYY-MM-DD)

**Ejemplo:**
```bash
curl "https://pqrs-backend-mvcp.onrender.com/api/contratacion/proxy?nit_entidad=891801994&limit=50&fecha_desde=2024-01-01"
```

### Endpoints de Migraciones
```
GET  /api/migrations/status  # Ver estado
POST /api/migrations/run     # Ejecutar migraciones
```

**Headers requeridos:**
```
X-Migration-Key: tu-clave-secreta
```

## 🔒 Seguridad

### Clave de Migración
- La clave debe estar en variable de entorno `MIGRATION_SECRET_KEY`
- **NO** commitear la clave en el código
- Cambiar la clave en producción

### CORS
- Backend acepta requests desde dominios configurados en `ALLOWED_ORIGINS`
- Automáticamente agrega variantes con/sin www

## 🐛 Troubleshooting

### Error: "Clave de migración inválida"
```bash
# Verificar que MIGRATION_KEY coincida con la configurada en Render
echo $MIGRATION_KEY
```

### Error: "No se pudo cargar la información de contratación"
1. Verificar que el NIT de la entidad esté configurado
2. Ir a Super Admin > Editar Entidad > Agregar NIT
3. El NIT debe existir en SECOP II

### Error: "CORS policy"
1. Verificar `ALLOWED_ORIGINS` en variables de entorno de Render
2. Debe incluir el dominio del frontend

### Frontend no compila
```bash
cd frontend/pqrs-frontend
rm -rf node_modules package-lock.json
npm install
ng serve
```

## 📝 Notas Importantes

1. **Sin cambios en BD**: Este módulo NO modifica la estructura de la base de datos
2. **API Externa**: Los datos vienen de SECOP II (datos.gov.co)
3. **Campo NIT**: Solo se requiere que la tabla `entities` tenga el campo `nit`
4. **Rate Limiting**: SECOP II puede tener límites de rate, considerar caché en futuro
5. **Datos en Tiempo Real**: No se almacenan datos de contratación localmente

## 🎯 Próximos Pasos

1. [ ] Implementar caché de consultas SECOP II (Redis)
2. [ ] Agregar exportación a PDF de reportes
3. [ ] Implementar notificaciones de contratos vencidos
4. [ ] Dashboard de analítica avanzada
5. [ ] Integración con otros sistemas de contratación

## 📞 Soporte

Para problemas o dudas:
1. Revisar logs en Render Dashboard
2. Verificar configuración de variables de entorno
3. Consultar documentación de SECOP II: https://www.datos.gov.co
