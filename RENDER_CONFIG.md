# 🔧 Configuración de Variables de Entorno en Render

## 🚨 Problema Actual

El backend en producción está rechazando peticiones del frontend debido a:
1. **CORS no configurado** correctamente para `https://pqrs-frontend.onrender.com`
2. **Base de datos sin migrar** (columnas `cedula`, `telefono`, `direccion` faltantes)

---

## 📋 Paso 1: Configurar Variables de Entorno

### Ir a Render Dashboard - Backend Service

1. Ve a tu servicio **pqrs-backend** en Render
2. Click en la pestaña **"Environment"** en el menú lateral
3. Agregar/Actualizar las siguientes variables:

### Variables Requeridas:

#### 1. ALLOWED_ORIGINS
```
Key: ALLOWED_ORIGINS
Value: http://localhost:4200,https://pqrs-frontend.onrender.com
```
**Importante:** Si tu frontend usa un dominio personalizado, agrégalo aquí separado por coma.

#### 2. SECRET_KEY (si no existe)
```
Key: SECRET_KEY
Value: [genera un string aleatorio largo y único]
```
Puedes generar uno con Python:
```python
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

#### 3. ENVIRONMENT (si no existe)
```
Key: ENVIRONMENT
Value: production
```

#### 4. DEBUG (si no existe)
```
Key: DEBUG
Value: false
```

### Variables Automáticas (NO tocar):
- ✅ `DATABASE_URL` - Render lo configura automáticamente desde tu PostgreSQL
- ✅ `PYTHON_VERSION` - Configurado desde runtime.txt

---

## 📋 Paso 2: Ejecutar Migración de Base de Datos

### Opción A: Desde Shell de Render (Recomendado)

1. En tu servicio **pqrs-backend**, click en **"Shell"**
2. Ejecuta:
```bash
cd /opt/render/project/src/backend/migrations
python3 migrate_postgres.py
```

3. Verifica el output:
```
✅ Conexión exitosa
✅ Valor 'CIUDADANO' agregado al ENUM
✅ Columna 'cedula' agregada
✅ Columna 'telefono' agregada
✅ Columna 'direccion' agregada
✅ ¡Migración completada exitosamente!
```

### Opción B: SQL Directo (Alternativa)

Si prefieres ejecutar SQL directamente:

1. Conecta a tu PostgreSQL con las credenciales de Render
2. Ejecuta este SQL:

```sql
-- 1. Agregar valor al ENUM
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_enum
        WHERE enumlabel = 'CIUDADANO'
        AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'userrole')
    ) THEN
        ALTER TYPE userrole ADD VALUE 'CIUDADANO';
    END IF;
END$$;

-- 2. Agregar columnas
ALTER TABLE users ADD COLUMN IF NOT EXISTS cedula VARCHAR(20);
ALTER TABLE users ADD COLUMN IF NOT EXISTS telefono VARCHAR(20);
ALTER TABLE users ADD COLUMN IF NOT EXISTS direccion VARCHAR(255);

-- 3. Crear índice
CREATE INDEX IF NOT EXISTS idx_users_cedula ON users(cedula);
```

---

## 📋 Paso 3: Reiniciar el Servicio

Después de configurar las variables de entorno:

1. En tu servicio **pqrs-backend**
2. Click en **"Manual Deploy"** → **"Clear build cache & deploy"**
3. Espera a que termine el deploy (3-5 minutos)

**Alternativa:** Render reiniciará automáticamente cuando cambies variables de entorno.

---

## 🔍 Verificación

### 1. Verificar CORS en los Logs

Busca en los logs de **pqrs-backend**:
```
INFO:     Uvicorn running on http://0.0.0.0:10000
```

Y NO deberías ver:
```
❌ CORS policy: No 'Access-Control-Allow-Origin'
```

### 2. Verificar Base de Datos

En los logs NO deberías ver:
```
❌ column users.cedula does not exist
❌ UndefinedColumn
❌ ProgrammingError
```

### 3. Probar el Frontend

1. Abre: https://pqrs-frontend.onrender.com
2. Abre la consola del navegador (F12)
3. Intenta hacer login
4. Deberías ver:
   - ✅ `200 OK` en las peticiones
   - ✅ Sin errores CORS
   - ✅ Login funcional

---

## 🎯 Checklist de Configuración

**Variables de Entorno:**
- [ ] `ALLOWED_ORIGINS` configurada con frontend URL
- [ ] `SECRET_KEY` configurada (única y segura)
- [ ] `ENVIRONMENT=production`
- [ ] `DEBUG=false`
- [ ] `DATABASE_URL` verificada (automática)

**Base de Datos:**
- [ ] Migración ejecutada (migrate_postgres.py)
- [ ] Columnas cedula/telefono/direccion agregadas
- [ ] Valor CIUDADANO agregado al ENUM
- [ ] Índice idx_users_cedula creado

**Deployment:**
- [ ] Backend rebuildeado después de cambios
- [ ] Frontend funcional (sin errores CORS)
- [ ] Login administrativo funcional
- [ ] Portal ciudadano funcional

---

## 🚨 Troubleshooting

### Si sigue habiendo errores CORS:

1. **Verifica la variable ALLOWED_ORIGINS:**
   ```bash
   # En Shell de Render:
   echo $ALLOWED_ORIGINS
   ```
   Debe mostrar: `http://localhost:4200,https://pqrs-frontend.onrender.com`

2. **Verifica que el servicio se reinició:**
   - Los cambios en variables de entorno requieren reinicio
   - Render lo hace automáticamente, pero puede tardar 1-2 minutos

3. **Si el frontend usa un dominio personalizado:**
   - Agrega ese dominio a `ALLOWED_ORIGINS`
   - Ejemplo: `http://localhost:4200,https://pqrs-frontend.onrender.com,https://tu-dominio.com`

### Si sigue el error de columnas:

1. **La migración no se ejecutó:**
   - Verifica que ejecutaste el script en Shell
   - Revisa el output completo del script
   - Verifica que no haya errores de permisos

2. **Ejecutar verificación manual:**
   ```sql
   SELECT column_name 
   FROM information_schema.columns 
   WHERE table_name = 'users' AND column_name IN ('cedula', 'telefono', 'direccion');
   ```
   Debe retornar las 3 columnas.

### Si hay error 500 en login:

Esto usualmente significa que la migración no se completó. Los logs del backend mostrarán:
```
psycopg2.errors.UndefinedColumn) column users.cedula does not exist
```

**Solución:** Ejecutar la migración (Paso 2).

---

## 📝 Resumen de Cambios Aplicados

### Backend Code Changes:
- ✅ `settings.py` - Actualizado CORS para soportar múltiples orígenes
- ✅ `.env.example` - Documentación de variables requeridas
- ✅ Migración PostgreSQL lista para ejecutar

### Commits:
- Commit pendiente con estos cambios

### Siguiente Paso:
1. Hacer commit y push de estos cambios
2. Configurar variables en Render Dashboard
3. Ejecutar migración de DB
4. Verificar funcionamiento
