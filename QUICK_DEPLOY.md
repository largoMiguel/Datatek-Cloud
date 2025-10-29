# 🚀 Quick Deploy - Módulo de Contratación

## Pasos Rápidos para Deployment

### 1️⃣ Configurar Variables de Entorno en Render

**Backend Service:**
```bash
MIGRATION_SECRET_KEY=genera-una-clave-segura-aqui
DATABASE_URL=(ya configurada)
SECRET_KEY=(ya configurada)
ALLOWED_ORIGINS=https://pqrs-frontend.onrender.com
```

### 2️⃣ Deploy Automático

```bash
# Hacer commit y push
git add .
git commit -m "feat: Módulo de Contratación con filtros y alertas"
git push origin master
```

Render detectará el push y desplegará automáticamente.

### 3️⃣ Ejecutar Migraciones (Opcional)

Como este módulo NO requiere cambios en BD, este paso es opcional:

```bash
cd backend
export MIGRATION_KEY="tu-clave-secreta"
./run_migration_prod.sh
```

O con curl:
```bash
curl -X POST https://pqrs-backend-mvcp.onrender.com/api/migrations/run \
  -H "X-Migration-Key: tu-clave-secreta" | jq '.'
```

### 4️⃣ Verificar Funcionamiento

**Backend:**
```bash
curl https://pqrs-backend-mvcp.onrender.com/health
```

**Frontend:**
- Abrir: https://pqrs-frontend.onrender.com
- Login → Dashboard → Contratación
- Verificar que carga datos

## ✅ Checklist Pre-Deploy

- [ ] Variables de entorno configuradas en Render
- [ ] Git push realizado
- [ ] Build exitoso en Render (revisar logs)
- [ ] Health check OK
- [ ] Frontend carga correctamente
- [ ] Módulo de Contratación accesible

## 🔍 Verificación Post-Deploy

```bash
# 1. Backend health
curl https://pqrs-backend-mvcp.onrender.com/health

# 2. Endpoint de contratación
curl "https://pqrs-backend-mvcp.onrender.com/api/contratacion/proxy?nit_entidad=891801994&limit=5"

# 3. Estado de migraciones
curl -X GET https://pqrs-backend-mvcp.onrender.com/api/migrations/status \
  -H "X-Migration-Key: tu-clave-secreta"
```

## 📋 Configuración del NIT en la Entidad

1. Login como superadmin
2. Ir a Super Admin
3. Editar entidad
4. Agregar NIT de la alcaldía
5. Guardar

El NIT se usará para consultar SECOP II.

## 🐛 Problemas Comunes

**Build falla en frontend:**
```bash
# Localmente
cd frontend/pqrs-frontend
npm install
ng build --configuration production
```

**Backend no arranca:**
- Revisar logs en Render Dashboard
- Verificar DATABASE_URL
- Verificar que todas las variables estén configuradas

**No carga datos de contratación:**
- Verificar que el NIT esté configurado en la entidad
- Probar el NIT en SECOP II: https://www.datos.gov.co

## 📚 Documentación Completa

Ver `MIGRATION_GUIDE.md` para detalles completos.
