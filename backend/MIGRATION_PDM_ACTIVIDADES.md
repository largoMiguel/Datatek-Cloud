# Migración: Campos de Actividades PDM (anio, meta_ejecutar, valor_ejecutado)

Esta migración agrega tres columnas a la tabla `pdm_actividades` para soportar actividades por año con metas ejecutables:

- `anio` (INTEGER)
- `meta_ejecutar` (FLOAT/REAL, default 0.0)
- `valor_ejecutado` (FLOAT/REAL, default 0.0)

## 🧪 Entorno Local

1) Ejecutar migración local

```bash
cd backend
python -m scripts.migrate_pdm_actividades_fields
# o alternativamente
python add_anio_meta_valor_to_pdm_actividades.py
```

2) Verificar campos en la tabla `pdm_actividades` (opcional)

```bash
# PostgreSQL (psql)
\d+ pdm_actividades

# SQLite (sqlite3)
.schema pdm_actividades
```

## ☁️ Producción (Render)

Esta migración ya está integrada en el endpoint `/api/migrations/run`. Solo ejecuta:

```bash
# Ver estado actual
curl -X GET \
  "$BACKEND_URL/api/migrations/status" \
  -H "X-Migration-Key: $MIGRATION_KEY" | jq '.'

# Ejecutar migraciones (incluye los nuevos campos de actividades)
curl -X POST \
  "$BACKEND_URL/api/migrations/run" \
  -H "X-Migration-Key: $MIGRATION_KEY" | jq '.'
```

O usa el script:

```bash
cd backend
export BACKEND_URL="https://<tu-backend>.onrender.com"
export MIGRATION_KEY="<tu-clave>"
./run_migration_prod.sh
```

## ✅ Post-migración

- Crear una actividad con "Meta a Ejecutar" > 0 y volver a editarla: el valor debe persistir (no debe verse "0").
- Registrar un avance: ahora te pide seleccionar la actividad; el valor ejecutado se toma de `meta_ejecutar` de esa actividad.
