# Migración: Permisos Modulares por Usuario

## Descripción
Esta migración añade soporte para permisos modulares granulares en la tabla `users`:
- `user_type`: Tipo de usuario (secretario/contratista)
- `allowed_modules`: Array JSON de módulos permitidos (pqrs, planes_institucionales, contratacion)

## Cambios en Base de Datos

### Tabla `users`:
```sql
-- PostgreSQL
ALTER TABLE users ADD COLUMN user_type usertype;  -- ENUM('secretario', 'contratista')
ALTER TABLE users ADD COLUMN allowed_modules JSON;  -- Array de strings

-- SQLite (desarrollo)
ALTER TABLE users ADD COLUMN user_type VARCHAR(20);
ALTER TABLE users ADD COLUMN allowed_modules TEXT;  -- JSON serializado
```

## Ejecución en Producción

### 1. Verificar Estado Actual

```bash
curl -X GET https://tu-backend.onrender.com/api/migrations/status \
  -H "X-Migration-Key: TU_CLAVE_SECRETA"
```

**Respuesta esperada:**
```json
{
  "database_connection": "✅ Conectado",
  "pending_migrations": ["add_user_type_column", "add_allowed_modules_column"],
  "last_migration": "Permisos modulares (user_type y allowed_modules)",
  "nit_field": "✅ Campo 'nit' existe en tabla entities",
  "enable_contratacion_field": "✅ Campo 'enable_contratacion' existe en entities",
  "user_type_field": "⚠️ Campo 'user_type' no encontrado - se requiere migración",
  "allowed_modules_field": "⚠️ Campo 'allowed_modules' no encontrado - se requiere migración"
}
```

### 2. Ejecutar Migración

```bash
curl -X POST https://tu-backend.onrender.com/api/migrations/run \
  -H "X-Migration-Key: TU_CLAVE_SECRETA"
```

**Respuesta esperada:**
```json
{
  "status": "success",
  "message": "Migraciones ejecutadas correctamente",
  "migrations": [
    "✅ Conexión a base de datos verificada",
    "ℹ️ Columna 'nit' ya existe en entities",
    "ℹ️ Columna 'enable_contratacion' ya existe en entities",
    "🆕 Agregada columna 'user_type' en users (secretario/contratista)",
    "🆕 Agregada columna 'allowed_modules' en users (array JSON de módulos)"
  ],
  "details": "Migraciones aplicadas: NIT, enable_contratacion, user_type y allowed_modules (si estaban pendientes)."
}
```

### 3. Verificar Migración Completada

```bash
curl -X GET https://tu-backend.onrender.com/api/migrations/status \
  -H "X-Migration-Key: TU_CLAVE_SECRETA"
```

**Respuesta esperada (después de migración):**
```json
{
  "database_connection": "✅ Conectado",
  "pending_migrations": [],
  "last_migration": "Permisos modulares (user_type y allowed_modules)",
  "nit_field": "✅ Campo 'nit' existe en tabla entities",
  "enable_contratacion_field": "✅ Campo 'enable_contratacion' existe en entities",
  "user_type_field": "✅ Campo 'user_type' existe en tabla users",
  "allowed_modules_field": "✅ Campo 'allowed_modules' existe en tabla users"
}
```

## Configuración de Clave de Migración

### Variables de Entorno en Render

En tu servicio de Render, agrega la variable:
```
MIGRATION_SECRET_KEY=<genera-una-clave-segura-aquí>
```

**Generar clave segura:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Compatibilidad con Datos Existentes

### Usuarios Existentes (Legacy):
- `user_type`: NULL → Se comportan como antes
- `allowed_modules`: NULL o [] → Acceso completo a módulos activos de la entidad

### Admins:
- **Siempre** tienen acceso a todos los módulos (bypass de `allowed_modules`)
- No se ven afectados por esta migración

### Nuevos Usuarios:
- **Secretarios/Contratistas**: Deben tener `user_type` y `allowed_modules` definidos
- Backend valida que los módulos asignados estén activos en la entidad

## Rollback (Si es necesario)

**⚠️ Solo en caso de emergencia:**

```sql
-- PostgreSQL
ALTER TABLE users DROP COLUMN IF EXISTS user_type;
ALTER TABLE users DROP COLUMN IF EXISTS allowed_modules;
DROP TYPE IF EXISTS usertype;

-- SQLite
-- No soporta DROP COLUMN directamente, requiere recrear tabla
```

## Testing Post-Migración

### 1. Crear Usuario con Permisos Limitados

```bash
curl -X POST https://tu-backend.onrender.com/api/users/ \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test_contratista",
    "email": "test@entity.gov.co",
    "password": "Test1234!",
    "role": "secretario",
    "entity_id": 1,
    "user_type": "contratista",
    "allowed_modules": ["planes_institucionales"]
  }'
```

### 2. Login como Usuario Limitado

```bash
curl -X POST https://tu-backend.onrender.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test_contratista",
    "password": "Test1234!"
  }'
```

### 3. Verificar en Frontend

- Solo debe ver pestaña "Dashboard" y "Planes Institucionales"
- NO debe ver pestañas de PQRS ni Contratación
- Navegación directa a rutas bloqueadas debe redirigir al dashboard

## Monitoreo

### Logs a Verificar:
```bash
# En Render logs
INFO - Migraciones ejecutadas exitosamente
```

### Errores Comunes:

**Error: "duplicate_object"**
```
El ENUM 'usertype' ya existe (PostgreSQL)
Solución: Ignorar, es normal si se ejecuta dos veces
```

**Error: "column already exists"**
```
La columna ya fue agregada anteriormente
Solución: Verificar con /status, probablemente ya está aplicada
```

## Documentación Relacionada

- `FIX_PERMISOS_MODULARES.md` - Corrección del bug de visualización
- `PERMISOS_MODULARES_USUARIOS.md` - Documentación completa de la feature
- `backend/app/routes/migrations.py` - Código de migración

## Soporte

Si algo falla:
1. Verificar logs en Render Dashboard
2. Ejecutar `/api/migrations/status` para ver estado
3. Revisar que `MIGRATION_SECRET_KEY` esté configurada
4. Validar que el usuario admin tenga permisos

## Checklist de Deployment

- [ ] Backup de base de datos de producción
- [ ] Variable `MIGRATION_SECRET_KEY` configurada en Render
- [ ] Ejecutar `/api/migrations/status` para ver estado actual
- [ ] Ejecutar `/api/migrations/run` para aplicar cambios
- [ ] Verificar con `/api/migrations/status` que todo esté ✅
- [ ] Testing manual: crear usuario con permisos limitados
- [ ] Validar en frontend que las pestañas se oculten correctamente
- [ ] Verificar que usuarios legacy sigan funcionando
- [ ] Documentar fecha y hora de ejecución

---

**Fecha de creación:** 29 de octubre de 2025  
**Versión:** 1.0  
**Autor:** Datatek Cloud  
**Estado:** ✅ Listo para producción
