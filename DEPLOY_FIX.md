# 🔧 Fix de Producción: Corrección de CORS y Environment

## 🐛 Problema Original
El frontend en producción estaba apuntando a `localhost:8000` en lugar de `https://pqrs-backend.onrender.com`, causando errores CORS:
```
Access to XMLHttpRequest at 'http://localhost:8000/api/auth/me' from origin 'https://pqrs-frontend.onrender.com' has been blocked by CORS policy
```

## ✅ Solución Aplicada
Se agregó `fileReplacements` en `angular.json` para que Angular use automáticamente `environment.prod.ts` cuando se compila para producción.

---

## 📋 Pasos para Aplicar el Fix en Render

### 1️⃣ Frontend (pqrs-frontend)

**Opción A: Trigger Manual Deploy (Recomendado)**
1. Ve a tu servicio **pqrs-frontend** en Render Dashboard
2. Click en **"Manual Deploy"** en el menú superior derecho
3. Selecciona **"Clear build cache & deploy"**
4. Espera a que termine el build (verás el mensaje "Build successful")

**Opción B: Desde la pestaña de Events**
1. Ve a tu servicio **pqrs-frontend**
2. Click en la pestaña **"Events"**
3. En el último commit (commit `a446356`), click en **"Deploy"**

### 2️⃣ Backend (pqrs-backend) - Migración de Base de Datos

**IMPORTANTE:** Antes de que el frontend funcione correctamente, debes ejecutar la migración de PostgreSQL.

**Método Recomendado: Shell de Render**
1. Ve a tu servicio **pqrs-backend** en Render Dashboard
2. Click en **"Shell"** en el menú lateral
3. Ejecuta:
   ```bash
   cd /opt/render/project/src/backend/migrations
   python3 migrate_postgres.py
   ```
4. Verifica que veas el mensaje: `✅ ¡Migración completada exitosamente!`

**Alternativa: SQL Directo**
Si prefieres ejecutar SQL directamente, consulta el archivo:
- `backend/migrations/MIGRATION_GUIDE.md` - Guía completa con múltiples métodos
- `backend/migrations/add_ciudadano_fields_postgres.sql` - Script SQL

---

## 🔍 Verificación Post-Deploy

### Verificar Frontend
1. Abre la consola del navegador en: https://pqrs-frontend.onrender.com
2. Intenta hacer login
3. **NO** deberías ver errores de:
   - ❌ `localhost:8000`
   - ❌ `CORS policy`
   - ❌ `net::ERR_FAILED`

4. Deberías ver requests a:
   - ✅ `https://pqrs-backend.onrender.com/api/auth/login`
   - ✅ `https://pqrs-backend.onrender.com/api/auth/me`

### Verificar Backend
1. Ve a los logs de **pqrs-backend** en Render
2. **NO** deberías ver:
   - ❌ `column users.cedula does not exist`
   - ❌ `ProgrammingError`
   - ❌ `UndefinedColumn`

3. Deberías ver:
   - ✅ `Application startup complete`
   - ✅ `GET /health HTTP/1.1" 200`
   - ✅ Sin errores de base de datos

---

## 🧪 Pruebas de Funcionalidad

### 1. Probar Login Administrativo
1. Ve a: https://pqrs-frontend.onrender.com/login
2. Intenta login con credenciales admin
3. Debería redirigir al dashboard sin errores

### 2. Probar Registro Ciudadano
1. Ve a: https://pqrs-frontend.onrender.com/portal-ciudadano
2. Click en "Crear Cuenta"
3. Llena el formulario con datos de prueba
4. Debería crear la cuenta exitosamente

### 3. Probar Ventanilla (Landing Page)
1. Ve a: https://pqrs-frontend.onrender.com/
2. Deberías ver la página de ventanilla con 4 opciones
3. Todos los botones deben funcionar sin errores de consola

---

## 📊 Checklist de Deploy

- [ ] **Commit pushed** a GitHub (commit `a446356`) ✅ HECHO
- [ ] **Frontend rebuildeado** en Render
- [ ] **Backend migración ejecutada** (agregar columnas cedula/telefono/direccion)
- [ ] **Frontend funcional** - Sin errores localhost/CORS
- [ ] **Backend funcional** - Sin errores de columnas faltantes
- [ ] **Login administrativo** funcionando
- [ ] **Registro ciudadano** funcionando
- [ ] **Ventanilla** funcionando

---

## ⚙️ Configuración Técnica Aplicada

### angular.json - Configuración de Production Build
```json
"production": {
  "fileReplacements": [
    {
      "replace": "src/environments/environment.ts",
      "with": "src/environments/environment.prod.ts"
    }
  ],
  ...
}
```

### Environments
- **Development** (`environment.ts`): `http://localhost:8000/api`
- **Production** (`environment.prod.ts`): `https://pqrs-backend.onrender.com/api`

### Comando de Build (Render ejecuta automáticamente)
```bash
npm run build
# Internamente ejecuta: ng build --configuration=production
```

---

## 🚨 Troubleshooting

### Si sigue apuntando a localhost:
1. Verifica que el build se haya ejecutado **después** del commit `a446356`
2. En Render, borra el cache: "Clear build cache & deploy"
3. Verifica en los logs del build que diga: `Using production configuration`

### Si hay errores de CORS diferentes:
Verifica que el backend tenga CORS configurado correctamente en `main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # O específicamente tu dominio de frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Si el backend sigue con error de columnas:
1. La migración NO se ejecutó
2. Sigue los pasos en `backend/migrations/MIGRATION_GUIDE.md`
3. Reinicia el servicio después de ejecutar la migración

---

## 📝 Commits Relacionados

- `a446356` - Fix: Configurar fileReplacements para environment.prod
- `ff1db7e` - Agregar scripts de migración PostgreSQL
- `7aa0d22` - Implementar sistema de portales duales

---

## 🎯 Resultado Esperado

Después de aplicar todos los pasos:
- ✅ Frontend apunta a `https://pqrs-backend.onrender.com/api`
- ✅ Sin errores CORS
- ✅ Backend con todas las columnas necesarias
- ✅ Login administrativo funcional
- ✅ Portal ciudadano funcional con registro
- ✅ Ventanilla funcional
