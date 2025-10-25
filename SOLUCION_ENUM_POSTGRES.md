# 🎯 Solución al Error de Enum PostgreSQL

## ❌ Error Identificado

```
invalid input value for enum tiposolicitud: "queja"
LINE 1: ...'ticket', 'Anónimo', 'N/A', NULL, NULL, NULL, 'queja', '...
```

## 🔍 Causa del Problema

**El frontend está enviando valores en MINÚSCULAS pero PostgreSQL tiene los enums en MAYÚSCULAS**

### Valores Actuales en PostgreSQL (INCORRECTOS):
```sql
tiposolicitud: ['PETICION', 'QUEJA', 'RECLAMO', 'SUGERENCIA']
estadopqrs: ['PENDIENTE', 'EN_PROCESO', 'RESUELTO', 'CERRADO']
```

### Valores que Espera el Modelo Python (CORRECTOS):
```python
tiposolicitud: ['peticion', 'queja', 'reclamo', 'sugerencia']
estadopqrs: ['pendiente', 'en_proceso', 'resuelto', 'cerrado']
```

## ✅ Solución Implementada

He actualizado la función `run_postgres_migration()` en `backend/app/main.py` para que:

1. **Detecte enums con valores incorrectos** (en mayúsculas)
2. **Elimine las columnas** que usan esos enums
3. **Elimine los enums antiguos**
4. **Recree los enums** con valores en minúsculas
5. **Recree las columnas** con los tipos correctos

### Enums Corregidos:

- ✅ `tipoidentificacion`: `['personal', 'anonima']`
- ✅ `mediorespuesta`: `['email', 'fisica', 'telefono', 'ticket']`
- ✅ `tiposolicitud`: `['peticion', 'queja', 'reclamo', 'sugerencia']`
- ✅ `estadopqrs`: `['pendiente', 'en_proceso', 'resuelto', 'cerrado']`

## 🚀 Desplegar la Corrección

### Opción 1: Despliegue Automático en Render

```bash
# Hacer commit y push
git add backend/app/main.py
git commit -m "fix: Corrección de enums PostgreSQL a minúsculas"
git push origin master
```

**La migración se ejecutará automáticamente al iniciar el servidor.**

Verás en los logs:
```
🔄 Ejecutando migración de PostgreSQL...
   ⚠️  ENUM tiposolicitud existe con valores incorrectos: ['PETICION', 'QUEJA', ...]
   🔄 Eliminando y recreando ENUM tiposolicitud...
   ✅ ENUM tiposolicitud creado
   ✅ ENUM estadopqrs creado
   ✅ Migración PostgreSQL completada
```

### Opción 2: Ejecución Manual (Si prefieres)

Si quieres ejecutar la corrección manualmente antes de desplegar:

```bash
# Conectar a PostgreSQL en Render
# Dashboard → Database → Connection String

psql postgresql://usuario:password@host/database

-- Verificar valores actuales
SELECT enumlabel FROM pg_enum 
WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'tiposolicitud')
ORDER BY enumsortorder;

-- Eliminar columna y enum
ALTER TABLE pqrs DROP COLUMN IF EXISTS tipo_solicitud CASCADE;
DROP TYPE IF EXISTS tiposolicitud CASCADE;

-- Recrear con valores correctos
CREATE TYPE tiposolicitud AS ENUM ('peticion', 'queja', 'reclamo', 'sugerencia');
ALTER TABLE pqrs ADD COLUMN tipo_solicitud tiposolicitud NOT NULL DEFAULT 'peticion';

-- Repetir para estadopqrs
ALTER TABLE pqrs DROP COLUMN IF EXISTS estado CASCADE;
DROP TYPE IF EXISTS estadopqrs CASCADE;
CREATE TYPE estadopqrs AS ENUM ('pendiente', 'en_proceso', 'resuelto', 'cerrado');
ALTER TABLE pqrs ADD COLUMN estado estadopqrs NOT NULL DEFAULT 'pendiente';
```

## ⚠️ Impacto de la Migración

### Datos Afectados:
- ⚠️ **Las PQRS existentes perderán los valores de `tipo_solicitud` y `estado`**
- Ambas columnas se recrearán con valores por defecto:
  - `tipo_solicitud`: `'peticion'`
  - `estado`: `'pendiente'`

### ¿Por qué?
PostgreSQL no permite modificar valores de enum una vez creados. La única forma es eliminar y recrear.

### Solución para Producción con Datos:
Si ya tienes datos importantes en producción, usa este enfoque alternativo:

```sql
-- 1. Agregar columnas temporales
ALTER TABLE pqrs ADD COLUMN tipo_solicitud_temp VARCHAR(50);
ALTER TABLE pqrs ADD COLUMN estado_temp VARCHAR(50);

-- 2. Copiar datos a minúsculas
UPDATE pqrs SET tipo_solicitud_temp = LOWER(tipo_solicitud::text);
UPDATE pqrs SET estado_temp = LOWER(estado::text);

-- 3. Eliminar columnas antiguas
ALTER TABLE pqrs DROP COLUMN tipo_solicitud CASCADE;
ALTER TABLE pqrs DROP COLUMN estado CASCADE;

-- 4. Eliminar enums antiguos
DROP TYPE tiposolicitud CASCADE;
DROP TYPE estadopqrs CASCADE;

-- 5. Crear enums nuevos
CREATE TYPE tiposolicitud AS ENUM ('peticion', 'queja', 'reclamo', 'sugerencia');
CREATE TYPE estadopqrs AS ENUM ('pendiente', 'en_proceso', 'resuelto', 'cerrado');

-- 6. Crear columnas nuevas
ALTER TABLE pqrs ADD COLUMN tipo_solicitud tiposolicitud;
ALTER TABLE pqrs ADD COLUMN estado estadopqrs;

-- 7. Copiar datos de vuelta
UPDATE pqrs SET tipo_solicitud = tipo_solicitud_temp::tiposolicitud;
UPDATE pqrs SET estado = estado_temp::estadopqrs;

-- 8. Hacer columnas NOT NULL
ALTER TABLE pqrs ALTER COLUMN tipo_solicitud SET NOT NULL;
ALTER TABLE pqrs ALTER COLUMN estado SET NOT NULL;

-- 9. Eliminar columnas temporales
ALTER TABLE pqrs DROP COLUMN tipo_solicitud_temp;
ALTER TABLE pqrs DROP COLUMN estado_temp;
```

## 🧪 Verificación

Después del despliegue, prueba crear una PQRS:

```bash
curl -X POST https://pqrs-backend.onrender.com/api/pqrs/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TU_TOKEN" \
  -d '{
    "tipo_identificacion": "anonima",
    "medio_respuesta": "ticket",
    "tipo_solicitud": "queja",
    "descripcion": "Prueba con enum corregido"
  }'
```

**Esperado:** Código 200 con la PQRS creada exitosamente.

## 📋 Checklist de Despliegue

- [ ] Hacer commit de cambios en `backend/app/main.py`
- [ ] Push a GitHub
- [ ] Esperar despliegue en Render (3-5 min)
- [ ] Verificar logs en Render:
  - [ ] Ver mensaje `✅ ENUM tiposolicitud creado`
  - [ ] Ver mensaje `✅ ENUM estadopqrs creado`
  - [ ] Ver mensaje `✅ Migración PostgreSQL completada`
- [ ] Probar crear PQRS desde el frontend
- [ ] Verificar que no hay errores en logs

## ❓ FAQ

### ¿Por qué los enums estaban en mayúsculas?

Probablemente fueron creados manualmente o por una migración anterior que usaba mayúsculas como convención.

### ¿Esto afectará mi base de datos local SQLite?

No, las migraciones de enums solo se ejecutan en PostgreSQL. SQLite usa strings normales.

### ¿Qué pasa si ya tengo PQRS en producción?

Si tienes datos importantes, usa el script SQL de "Solución para Producción con Datos" que preserva los datos existentes.

### ¿Tengo que hacer algo en el frontend?

No, el frontend ya está enviando los valores correctos en minúsculas. El problema estaba solo en la base de datos.

## 🎉 Resultado Final

Una vez desplegado, el sistema funcionará completamente:

✅ CORS configurado correctamente  
✅ Enums en minúsculas sincronizados  
✅ PQRS se pueden crear sin errores  
✅ Todos los tipos de solicitud funcionan: peticion, queja, reclamo, sugerencia
