# 🚀 Guía de Despliegue en Render.com

Guía completa para desplegar tu aplicación PQRS en Render.com.

## 📋 Información de tu Base de Datos

Ya tienes una base de datos PostgreSQL configurada en Render:

```
Hostname: dpg-d3rs4oripnbc73esb06g-a.oregon-postgres.render.com
Port: 5432
Database: datatek_cloud
Username: datatek_cloud_user
Password: kkzJrjjJ1AD3RgKK0CFHdVFIAVhSPQKE

Internal Database URL:
postgresql://datatek_cloud_user:kkzJrjjJ1AD3RgKK0CFHdVFIAVhSPQKE@dpg-d3rs4oripnbc73esb06g-a.oregon-postgres.render.com:5432/datatek_cloud
```

## 🎯 Arquitectura del Despliegue

```
┌─────────────────────────────────────────┐
│          RENDER.COM                     │
├─────────────────────────────────────────┤
│                                         │
│  ┌──────────────┐    ┌──────────────┐  │
│  │ Web Service  │───►│  PostgreSQL  │  │
│  │   Backend    │    │   Database   │  │
│  │   FastAPI    │    │ (Ya creada)  │  │
│  └──────────────┘    └──────────────┘  │
│         │                               │
│  ┌──────▼───────┐                      │
│  │ Static Site  │                      │
│  │   Frontend   │                      │
│  │   Angular    │                      │
│  └──────────────┘                      │
│                                         │
└─────────────────────────────────────────┘
```

---

## 🚀 PARTE 1: DESPLEGAR BACKEND (10-15 min)

### Opción A: Despliegue Automático con render.yaml (Recomendado)

#### Paso 1: Preparar Repositorio

Tu repositorio ya está listo con:
- ✅ `render.yaml` - Configuración automática
- ✅ `backend/build.sh` - Script de build
- ✅ `backend/requirements.txt` - Dependencias
- ✅ `backend/.env.render` - Variables de entorno (referencia)

#### Paso 2: Conectar Repositorio a Render

1. **Ve a https://dashboard.render.com**
2. **Regístrate o inicia sesión** (puedes usar GitHub)
3. **Click en "New +"** → **"Blueprint"**
4. **Connect a repository**:
   - Si no has conectado GitHub, click en "Connect GitHub"
   - Autoriza a Render
   - Busca tu repositorio: `largoMiguel/Datatek-Cloud`
   - Click en "Connect"

#### Paso 3: Configurar Blueprint

1. **Blueprint Name**: `pqrs-alcaldia`
2. **Branch**: `master`
3. Render detectará automáticamente el `render.yaml`
4. **Revisa la configuración**:
   - Service: `pqrs-backend` (Python)
   - Database: `pqrs-database` (PostgreSQL)

#### Paso 4: Configurar Variables de Entorno

Render te pedirá configurar las variables. Usa estos valores:

```env
DATABASE_URL=postgresql://datatek_cloud_user:kkzJrjjJ1AD3RgKK0CFHdVFIAVhSPQKE@dpg-d3rs4oripnbc73esb06g-a.oregon-postgres.render.com:5432/datatek_cloud

SECRET_KEY=1vEvfjQRvRDAe3pZEpYFElVLR3JE1B6b3k4xyrUHAz3f1-c4-7BSpNEdvnyXUUW_TNR-RqU5tOkSoPsJ0L6uhg

ALGORITHM=HS256

ACCESS_TOKEN_EXPIRE_MINUTES=30

HOST=0.0.0.0

PORT=8000

ENVIRONMENT=production

DEBUG=False

ALLOWED_ORIGINS=http://localhost:4200
```

**IMPORTANTE**: Actualiza `ALLOWED_ORIGINS` cuando tengas la URL del frontend.

#### Paso 5: Aplicar Blueprint

1. Click en **"Apply"**
2. Render comenzará a:
   - Crear el Web Service
   - Instalar dependencias
   - Conectar a la base de datos
   - Desplegar la aplicación

**Tiempo estimado**: 5-10 minutos

#### Paso 6: Verificar Despliegue

1. Ve a **Dashboard** → **pqrs-backend**
2. Espera a que el estado sea **"Live"** ✅
3. Copia la URL (algo como: `https://pqrs-backend.onrender.com`)
4. Verifica el health check:
   ```
   https://pqrs-backend.onrender.com/health
   ```
   Deberías ver: `{"status":"healthy"}`

5. Accede a la documentación:
   ```
   https://pqrs-backend.onrender.com/docs
   ```

---

### Opción B: Despliegue Manual (Alternativa)

Si prefieres configurar manualmente:

#### Paso 1: Crear Web Service

1. **Dashboard** → **New +** → **Web Service**
2. **Connect repository**: `largoMiguel/Datatek-Cloud`
3. **Configuración**:
   ```
   Name: pqrs-backend
   Region: Oregon (US West)
   Branch: master
   Root Directory: backend
   Runtime: Python 3
   Build Command: ./build.sh
   Start Command: gunicorn -k uvicorn.workers.UvicornWorker -w 4 -b 0.0.0.0:$PORT app.main:app --timeout 120
   Plan: Free
   ```

#### Paso 2: Variables de Entorno

En **Environment** → **Environment Variables**, agrega:

```
DATABASE_URL=postgresql://datatek_cloud_user:kkzJrjjJ1AD3RgKK0CFHdVFIAVhSPQKE@dpg-d3rs4oripnbc73esb06g-a.oregon-postgres.render.com:5432/datatek_cloud
SECRET_KEY=1vEvfjQRvRDAe3pZEpYFElVLR3JE1B6b3k4xyrUHAz3f1-c4-7BSpNEdvnyXUUW_TNR-RqU5tOkSoPsJ0L6uhg
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=production
DEBUG=False
ALLOWED_ORIGINS=http://localhost:4200
PYTHON_VERSION=3.11.9
```

#### Paso 3: Advanced Settings

```
Health Check Path: /health
Auto-Deploy: Yes (para que se actualice con cada push)
```

#### Paso 4: Create Web Service

Click en **"Create Web Service"** y espera el despliegue.

---

## 🌐 PARTE 2: DESPLEGAR FRONTEND (5-10 min)

### Paso 1: Preparar Frontend

En tu máquina local:

```bash
cd /Users/largo/Documents/SOLUCTIONS/pqrs-alcaldia/frontend/pqrs-frontend

# Actualizar environment.prod.ts con la URL del backend
nano src/environments/environment.prod.ts
```

Contenido:

```typescript
export const environment = {
  production: true,
  apiUrl: 'https://pqrs-backend.onrender.com/api', // Tu URL de backend
  openaiApiKey: '' // Opcional
};
```

### Paso 2: Compilar para Producción

```bash
npm install
npm run build:prod
```

Los archivos compilados estarán en: `dist/pqrs-frontend/browser/`

### Paso 3: Crear Static Site en Render

1. **Dashboard** → **New +** → **Static Site**
2. **Connect repository**: `largoMiguel/Datatek-Cloud`
3. **Configuración**:
   ```
   Name: pqrs-frontend
   Branch: master
   Root Directory: frontend/pqrs-frontend
   Build Command: npm install && npm run build:prod
   Publish Directory: dist/pqrs-frontend/browser
   ```

4. **Create Static Site**

### Paso 4: Actualizar CORS en Backend

Una vez que tengas la URL del frontend (ej: `https://pqrs-frontend.onrender.com`):

1. Ve a **Dashboard** → **pqrs-backend**
2. **Environment** → Edita `ALLOWED_ORIGINS`:
   ```
   ALLOWED_ORIGINS=https://pqrs-frontend.onrender.com,http://localhost:4200
   ```
3. Guarda y el servicio se reiniciará automáticamente

---

## ✅ VERIFICACIÓN COMPLETA

### Backend
```bash
# Health check
curl https://pqrs-backend.onrender.com/health

# Documentación
# Abre en navegador: https://pqrs-backend.onrender.com/docs
```

### Frontend
```bash
# Abre en navegador: https://pqrs-frontend.onrender.com
# Login con:
Usuario: admin
Password: admin123
```

### Base de Datos
```bash
# Desde tu máquina local (opcional)
PGPASSWORD=kkzJrjjJ1AD3RgKK0CFHdVFIAVhSPQKE psql -h dpg-d3rs4oripnbc73esb06g-a.oregon-postgres.render.com -U datatek_cloud_user datatek_cloud

# Ver tablas
\dt

# Salir
\q
```

---

## 🔄 ACTUALIZACIONES FUTURAS

### Actualización Automática (Recomendado)

Render se actualiza automáticamente con cada `git push`:

```bash
# Hacer cambios en tu código
git add .
git commit -m "Descripción de cambios"
git push origin master

# Render detectará el push y desplegará automáticamente
```

### Actualización Manual

Si deshabilitaste auto-deploy:

1. Ve a **Dashboard** → Tu servicio
2. Click en **"Manual Deploy"** → **"Deploy latest commit"**

---

## 🐛 TROUBLESHOOTING

### Backend no inicia

**Ver logs**:
1. Dashboard → pqrs-backend
2. Pestaña "Logs"
3. Busca errores en rojo

**Causas comunes**:
- Variables de entorno incorrectas
- DATABASE_URL mal configurada
- Dependencias faltantes

**Solución**:
```bash
# Verificar que todas las variables estén configuradas
# Verificar que DATABASE_URL sea la Internal Database URL
```

### Frontend no carga la API

**Verificar CORS**:
1. Abre la consola del navegador (F12)
2. Busca errores de CORS
3. Verifica que `ALLOWED_ORIGINS` en backend incluya la URL del frontend

### Base de datos no conecta

**Verificar conexión**:
```bash
# Desde tu terminal local
PGPASSWORD=kkzJrjjJ1AD3RgKK0CFHdVFIAVhSPQKE psql -h dpg-d3rs4oripnbc73esb06g-a.oregon-postgres.render.com -U datatek_cloud_user datatek_cloud -c "SELECT version();"
```

### Error 502 Bad Gateway

El servicio está iniciando. Espera 1-2 minutos.

---

## 💡 CONSEJOS Y MEJORES PRÁCTICAS

### 1. Plan Gratuito de Render

**Limitaciones**:
- El servicio se "duerme" después de 15 minutos de inactividad
- Primera petición después de dormir tarda ~30 segundos
- 750 horas gratis al mes

**Solución**: Upgrade a plan Starter ($7/mes) para mantenerlo siempre activo

### 2. Variables de Entorno Sensibles

- ❌ NO incluyas passwords en el código
- ✅ Usa las Environment Variables de Render
- ✅ El archivo `.env.render` es solo referencia (no se sube a git)

### 3. Logs y Monitoreo

```bash
# Ver logs en tiempo real
# Dashboard → Service → Logs (en vivo)

# Descargar logs
# Dashboard → Service → Logs → Download
```

### 4. Dominios Personalizados

Render te da un subdominio gratis:
- Backend: `pqrs-backend.onrender.com`
- Frontend: `pqrs-frontend.onrender.com`

Para dominio personalizado:
1. Dashboard → Service → Settings → Custom Domain
2. Agrega tu dominio
3. Configura DNS según instrucciones

### 5. HTTPS

✅ Render proporciona HTTPS gratis con certificados SSL automáticos

### 6. Backups de Base de Datos

En Render Dashboard:
1. Database → Backups
2. Habilitar backups automáticos
3. O crear backup manual

---

## 💰 COSTOS ESTIMADOS

### Plan Gratuito (Recomendado para empezar)
```
Backend Web Service: $0/mes (con limitaciones)
Frontend Static Site: $0/mes
PostgreSQL Database: $0/mes (limite de 90 días, luego $7/mes)
Total: $0/mes inicialmente
```

### Plan Básico de Producción
```
Backend Starter: $7/mes (siempre activo)
Frontend Pro: $0-1/mes (static site)
PostgreSQL Starter: $7/mes (1GB RAM, 10GB storage)
Total: ~$14-15/mes
```

---

## 📚 RECURSOS ADICIONALES

- **Render Docs**: https://render.com/docs
- **FastAPI Deployment**: https://fastapi.tiangolo.com/deployment/
- **Render PostgreSQL**: https://render.com/docs/databases
- **Tu Repositorio**: https://github.com/largoMiguel/Datatek-Cloud

---

## 📞 SOPORTE

- **Render Status**: https://status.render.com
- **Community Forum**: https://community.render.com
- **Support**: Dashboard → Help

---

## ✅ CHECKLIST FINAL

- [ ] Repositorio pusheado a GitHub
- [ ] Blueprint aplicado en Render
- [ ] Backend desplegado y "Live"
- [ ] Health check funcionando
- [ ] Frontend compilado y desplegado
- [ ] CORS configurado correctamente
- [ ] Base de datos conectada
- [ ] Usuario admin funciona (admin/admin123)
- [ ] Cambiar contraseña de admin
- [ ] Configurar backups de base de datos

---

🎉 **¡Felicitaciones! Tu aplicación PQRS está en producción en Render.com**

URLs de tu aplicación:
- **Backend**: https://pqrs-backend.onrender.com
- **Frontend**: https://pqrs-frontend.onrender.com
- **API Docs**: https://pqrs-backend.onrender.com/docs
