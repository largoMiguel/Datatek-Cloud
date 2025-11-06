# 🚀 Migración Completa de Base de Datos - Producción

## 📋 Descripción

Este sistema ejecuta una **migración completa e idempotente** de la base de datos en producción. La migración:

- ✅ Crea todas las tablas faltantes
- ✅ Agrega columnas faltantes a tablas existentes
- ✅ Convierte tipos ENUM problemáticos a TEXT
- ✅ Crea índices para optimización
- ✅ Mantiene integridad referencial
- ✅ Es **100% idempotente** (se puede ejecutar múltiples veces sin problemas)
- ✅ No elimina datos existentes

## 🔐 Configuración de Seguridad

### Variables de Entorno Requeridas

Asegúrate de tener configuradas estas variables en tu archivo `.env` o en Render:

```bash
# Base de datos (Render la configura automáticamente)
DATABASE_URL=postgresql://user:password@host/dbname

# Clave secreta para migraciones (IMPORTANTE)
MIGRATION_SECRET_KEY=tu-clave-secreta-2024
```

**⚠️ IMPORTANTE:** La clave `MIGRATION_SECRET_KEY` es requerida para ejecutar las migraciones. Por defecto es `tu-clave-secreta-2024`.

## 🌐 URLs de Producción

- **Backend:** https://pqrs-backend.onrender.com
- **Frontend:** https://pqrs-frontend.onrender.com

## 📡 Endpoints Disponibles

### 1. Verificar Estado de la Base de Datos

**No requiere autenticación** - Útil para debugging y monitoreo

```bash
curl -X GET https://pqrs-backend.onrender.com/api/migrations/status
```

**Respuesta:**
```json
{
  "status": "ok",
  "database_connected": true,
  "statistics": {
    "total_tables": 15,
    "expected_tables": 15,
    "existing_tables": 15,
    "completeness_percentage": 100.0
  },
  "tables_by_module": {
    "core": {
      "entities": true,
      "users": true,
      "secretarias": true
    },
    "pqrs": {
      "pqrs": true
    },
    "planes": {
      "planes_institucionales": true,
      "componentes_procesos": true,
      "actividades": true,
      "actividades_ejecucion": true,
      "actividades_evidencias": true
    },
    "pdm": {
      "pdm_archivos_excel": true,
      "pdm_meta_assignments": true,
      "pdm_avances": true,
      "pdm_actividades": true,
      "pdm_actividades_ejecuciones": true,
      "pdm_actividades_evidencias": true
    }
  },
  "record_counts": {
    "entities": 3,
    "users": 15,
    "secretarias": 8,
    "pqrs": 45,
    "planes_institucionales": 2
  },
  "migration_history": {
    "running": false,
    "last_run": "2024-11-05T14:30:00",
    "last_result": "success"
  }
}
```

### 2. Ejecutar Migración Completa

**Requiere autenticación con X-Migration-Key header**

```bash
curl -X POST https://pqrs-backend.onrender.com/api/migrations/run/status \
     -H "X-Migration-Key: tu-clave-secreta-2024" \
     -H "Content-Type: application/json"
```

**Respuesta exitosa:**
```json
{
  "status": "success",
  "message": "✓ Migración completada exitosamente",
  "timestamp": "2024-11-05T14:30:00",
  "total_results": 156,
  "total_errors": 0,
  "results": [
    "✓ Tablas base creadas/verificadas con SQLAlchemy",
    "✓ Tabla entities existe",
    "✓ Tabla users existe",
    "✓ users.role convertido a TEXT",
    "✓ Columna entity_id agregada a planes_institucionales",
    "✓ Migración de Planes Institucionales completada",
    "✓ Migración de PDM completada",
    "✓ Base de datos tiene 15 tablas"
  ],
  "errors": [],
  "logs": [
    "[2024-11-05 14:30:00] INICIANDO MIGRACIÓN COMPLETA",
    "[2024-11-05 14:30:01] ✓ Tablas base creadas correctamente",
    "[2024-11-05 14:30:02] Convirtiendo users.role de ENUM a TEXT...",
    "[2024-11-05 14:30:03] ✓ users.role convertido a TEXT",
    "[2024-11-05 14:30:10] ✓✓✓ MIGRACIÓN COMPLETADA EXITOSAMENTE ✓✓✓"
  ]
}
```

**Respuesta con errores:**
```json
{
  "status": "error",
  "message": "❌ Error crítico en migración: ...",
  "timestamp": "2024-11-05T14:30:00",
  "results": [...],
  "errors": [
    "[2024-11-05 14:30:05] ❌ Error convirtiendo columna: ..."
  ],
  "logs": [...],
  "traceback": "..."
}
```

## 🗂️ Estructura de Tablas Migradas

### Módulo Core
- **entities** - Entidades/Alcaldías
- **users** - Usuarios del sistema
- **secretarias** - Secretarías por entidad

### Módulo PQRS
- **pqrs** - Peticiones, Quejas, Reclamos y Sugerencias

### Módulo Alertas
- **alerts** - Sistema de notificaciones

### Módulo Planes Institucionales
- **planes_institucionales** - Planes estratégicos
- **componentes_procesos** - Componentes de planes
- **actividades** - Actividades de componentes
- **actividades_ejecucion** - Seguimiento de actividades
- **actividades_evidencias** - Evidencias de ejecución

### Módulo PDM (Plan de Desarrollo Municipal)
- **pdm_archivos_excel** - Archivos Excel del PDM
- **pdm_meta_assignments** - Asignación de metas
- **pdm_avances** - Avances por año
- **pdm_actividades** - Actividades del PDM
- **pdm_actividades_ejecuciones** - Historial de ejecuciones
- **pdm_actividades_evidencias** - Evidencias con imágenes

## 🔧 Solución de Problemas Conocidos

### Problema: ENUMs de PostgreSQL

**Síntoma:** Errores como `invalid input value for enum userrole: "SUPERADMIN"`

**Solución:** La migración automáticamente:
1. Detecta columnas con tipo ENUM
2. Crea columna temporal con tipo TEXT
3. Copia valores normalizados (minúsculas con guión bajo)
4. Elimina columna ENUM original
5. Renombra columna temporal
6. Elimina tipo ENUM de PostgreSQL

### Problema: Columnas Faltantes

**Síntoma:** Errores como `column "entity_id" does not exist`

**Solución:** La migración automáticamente:
- Detecta columnas faltantes comparando con modelos
- Agrega columnas con el tipo correcto
- Mantiene datos existentes intactos

### Problema: Tablas Faltantes

**Síntoma:** Errores como `relation "pdm_actividades" does not exist`

**Solución:** La migración automáticamente:
- Usa `Base.metadata.create_all()` para crear estructura base
- Crea tablas adicionales con SQL directo
- Configura claves foráneas y constraints

## 📊 Monitoreo Post-Migración

### 1. Verificar Salud de la Base de Datos

```bash
# Verificar conexión y tablas
curl https://pqrs-backend.onrender.com/api/migrations/status | jq '.statistics'
```

### 2. Verificar Conteo de Registros

```bash
# Ver cantidad de registros por tabla
curl https://pqrs-backend.onrender.com/api/migrations/status | jq '.record_counts'
```

### 3. Ver Logs de Última Migración

```bash
# Ver últimos logs
curl https://pqrs-backend.onrender.com/api/migrations/status | jq '.migration_history'
```

## 🎯 Casos de Uso

### Caso 1: Primera Migración en Base de Datos Vacía

```bash
# Ejecutar migración completa
curl -X POST https://pqrs-backend.onrender.com/api/migrations/run/status \
     -H "X-Migration-Key: tu-clave-secreta-2024"

# Resultado esperado: Todas las tablas creadas desde cero
```

### Caso 2: Actualizar Base de Datos Existente

```bash
# La migración es idempotente, detecta qué falta y solo agrega lo necesario
curl -X POST https://pqrs-backend.onrender.com/api/migrations/run/status \
     -H "X-Migration-Key: tu-clave-secreta-2024"

# Resultado esperado: Solo se agregan columnas/tablas faltantes
```

### Caso 3: Reparar ENUMs Problemáticos

```bash
# La migración detecta y convierte ENUMs a TEXT automáticamente
curl -X POST https://pqrs-backend.onrender.com/api/migrations/run/status \
     -H "X-Migration-Key: tu-clave-secreta-2024"

# Resultado esperado: ENUMs convertidos sin pérdida de datos
```

## ⚠️ Precauciones

1. **Backup:** Aunque la migración es segura, considera hacer backup antes de ejecutar en producción
2. **Tiempo de Ejecución:** La primera migración puede tomar 30-60 segundos
3. **No Interrumpir:** No interrumpas la migración mientras está en ejecución
4. **Verificar Logs:** Revisa los logs después de la migración para detectar warnings

## 🔄 Rollback

Si necesitas revertir cambios:

1. **Restaurar desde backup** (si existe)
2. **Ejecutar migración nuevamente** (es idempotente, corregirá inconsistencias)

## 📝 Notas Técnicas

- **Motor:** PostgreSQL (optimizado para Render)
- **ORM:** SQLAlchemy 2.x
- **Idempotencia:** Sí - puede ejecutarse múltiples veces
- **Transacciones:** Cada cambio usa transacciones individuales
- **Errores:** Los errores en una operación no detienen el resto
- **Logging:** Cada operación queda registrada en logs internos

## 🆘 Soporte

Si encuentras problemas:

1. Verifica el endpoint `/api/migrations/status`
2. Revisa los logs en la respuesta
3. Busca errores específicos en el campo `errors`
4. Contacta al equipo de desarrollo con los logs completos

---

**Última actualización:** 5 de noviembre de 2024
**Versión:** 2.0
**Autor:** Sistema PQRS Alcaldía
