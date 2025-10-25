# 🔴 Solución al Error CORS

## Error Actual

```
Access to XMLHttpRequest at 'https://pqrs-backend.onrender.com/api/pqrs/' 
from origin 'https://pqrs-frontend.onrender.com' has been blocked by CORS policy: 
No 'Access-Control-Allow-Origin' header is present on the requested resource.

POST https://pqrs-backend.onrender.com/api/pqrs/ net::ERR_FAILED 500 (Internal Server Error)
```

## 🎯 Causa del Problema

Este error tiene **DOS causas combinadas**:

1. ❌ **Error 500 en el servidor**: El backend está fallando antes de poder enviar respuesta
2. ❌ **CORS no configurado**: Incluso si funcionara, falta la configuración CORS

## ✅ Solución Implementada

He realizado los siguientes cambios en el código:

### 1. Middleware de Captura de Errores (`main.py`)
- ✅ Agrega headers CORS incluso cuando hay errores 500
- ✅ Registra errores con traceback completo para debugging
- ✅ Retorna respuestas JSON estructuradas

### 2. Manejo de Errores Robusto (`routes/pqrs.py`)
- ✅ Try-catch en validación de datos
- ✅ Try-catch en creación de PQRS
- ✅ Rollback automático en errores de DB
- ✅ Logging detallado de errores

### 3. Headers CORS Adicionales
- ✅ `expose_headers: ["*"]` para permitir lectura de todos los headers

---

## 🚀 Pasos para Desplegar la Solución

### Paso 1: Hacer push de los cambios

```bash
cd /Users/largo/Documents/SOLUCTIONS/pqrs-alcaldia

# Verificar cambios
git status

# Agregar archivos modificados
git add backend/app/main.py
git add backend/app/routes/pqrs.py
git add backend/RENDER_CONFIG.md
git add backend/validate_cors.py
git add backend/.env.render

# Commit
git commit -m "fix: Solución definitiva para error CORS y 500"

# Push a GitHub
git push origin master
```

### Paso 2: Configurar Variables de Entorno en Render

1. Ve a [Render Dashboard](https://dashboard.render.com/)
2. Selecciona tu servicio **pqrs-backend**
3. Ve a **Environment** en el menú lateral
4. Agrega/Verifica esta variable:

```
ALLOWED_ORIGINS=https://pqrs-frontend.onrender.com,http://localhost:4200
```

**⚠️ IMPORTANTE:**
- NO incluyas barra final en las URLs
- Usa comas sin espacios para separar múltiples orígenes
- Asegúrate de usar `https://` (no `http://`) para producción

5. Guarda los cambios (el servicio se reiniciará automáticamente)

### Paso 3: Verificar el Despliegue

Espera a que Render termine de desplegar (2-5 minutos). En los logs deberías ver:

```
🌐 CORS Origins configurados: ['https://pqrs-frontend.onrender.com', 'http://localhost:4200']
   Allowed Origins String: https://pqrs-frontend.onrender.com,http://localhost:4200
```

---

## 🔍 Diagnóstico del Error 500

El error 500 puede deberse a varios factores. Para diagnosticar:

### 1. Revisar Logs de Render

```
Dashboard → pqrs-backend → Logs
```

Busca líneas con `❌ Error` que mostrarán:
- Path de la petición
- Error específico
- Traceback completo

### 2. Problemas Comunes

#### A. Error de Base de Datos

**Síntoma:** `relation "pqrs" does not exist` o similar

**Solución:** Ejecutar migraciones
```bash
# En Render Shell o localmente
python -m alembic upgrade head
```

#### B. Error de Enum en PostgreSQL

**Síntoma:** `invalid input value for enum`

**Solución:** El código ya incluye migración automática para recrear enums. Verifica logs para ver si se ejecutó correctamente.

#### C. Error de Validación de Datos

**Síntoma:** `Error validando datos` en logs

**Solución:** Verifica que el frontend esté enviando todos los campos requeridos:
- `tipo_identificacion`: "personal" o "anonima"
- `medio_respuesta`: "email", "fisica", "telefono" o "ticket"
- `tipo_solicitud`: tipo válido de solicitud
- `descripcion`: no puede estar vacío

---

## 🧪 Pruebas Locales

Para probar localmente antes de desplegar:

### 1. Configurar entorno local

```bash
cd backend

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate  # macOS/Linux

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.render .env
# Editar .env con tus valores locales
```

### 2. Validar configuración CORS

```bash
python validate_cors.py
```

Deberías ver:
```
✅ Configuración CORS correcta

URLs permitidas:
   ✓ https://pqrs-frontend.onrender.com
   ✓ http://localhost:4200
```

### 3. Ejecutar servidor local

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Probar endpoint desde frontend local

Edita `frontend/pqrs-frontend/src/environments/environment.ts`:

```typescript
export const environment = {
  production: false,
  apiUrl: 'http://localhost:8000/api'
};
```

---

## 📞 Verificación Final

Una vez desplegado, prueba estos endpoints:

### 1. Health Check
```bash
curl https://pqrs-backend.onrender.com/health
```

**Esperado:** `{"status":"healthy"}`

### 2. CORS Preflight
```bash
curl -X OPTIONS https://pqrs-backend.onrender.com/api/pqrs/ \
  -H "Origin: https://pqrs-frontend.onrender.com" \
  -H "Access-Control-Request-Method: POST" \
  -i
```

**Esperado:** Headers con `Access-Control-Allow-Origin`

### 3. Login (para obtener token)
```bash
curl -X POST https://pqrs-backend.onrender.com/api/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

**Esperado:** Token JWT

### 4. Crear PQRS
```bash
curl -X POST https://pqrs-backend.onrender.com/api/pqrs/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TU_TOKEN_AQUI" \
  -H "Origin: https://pqrs-frontend.onrender.com" \
  -d '{
    "tipo_identificacion": "personal",
    "medio_respuesta": "email",
    "nombre_ciudadano": "Test User",
    "cedula_ciudadano": "123456789",
    "email_ciudadano": "test@example.com",
    "tipo_solicitud": "PETICION",
    "descripcion": "Test PQRS"
  }'
```

**Esperado:** PQRS creada exitosamente

---

## ❓ FAQ

### ¿Por qué sigo viendo el error después de los cambios?

1. **Caché del navegador**: Limpia caché o usa modo incógnito
2. **Variables no actualizadas**: Verifica en Render que `ALLOWED_ORIGINS` esté correcta
3. **Despliegue no completado**: Espera a que Render termine el deploy
4. **Error 500 persistente**: Revisa logs de Render para ver el error específico

### ¿Cómo sé si el problema es CORS o el error 500?

- **CORS**: Verás el error en la consola del navegador pero la petición llegó al servidor
- **Error 500**: Verás en logs de Render el error específico que causó el fallo

### ¿Qué hago si el error persiste?

1. Captura los logs completos de Render (sección Logs)
2. Captura la consola del navegador (F12 → Console)
3. Captura la pestaña Network (F12 → Network) de la petición fallida
4. Con esa información podemos diagnosticar el problema específico

---

## 📚 Referencias

- [FastAPI CORS Middleware](https://fastapi.tiangolo.com/tutorial/cors/)
- [MDN CORS](https://developer.mozilla.org/es/docs/Web/HTTP/CORS)
- [Render Environment Variables](https://render.com/docs/environment-variables)
