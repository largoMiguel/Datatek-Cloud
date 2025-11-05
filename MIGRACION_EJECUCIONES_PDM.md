# Migración de Ejecuciones PDM - Instrucciones de Producción

## 📋 Resumen
Esta migración introduce un sistema de historial de ejecuciones para el módulo PDM, permitiendo:
- Registrar múltiples ejecuciones por actividad con timestamps
- Cada ejecución puede tener evidencias (imágenes) asociadas
- El `valor_ejecutado` de una actividad se calcula como la suma de todas sus ejecuciones
- Historial completo visible en la interfaz

## 🔧 Cambios en la Base de Datos

### Nueva Tabla: `pdm_actividades_ejecuciones`
```sql
id SERIAL PRIMARY KEY
actividad_id INTEGER (FK → pdm_actividades)
entity_id INTEGER (FK → entities)
valor_ejecutado_incremento DOUBLE PRECISION
descripcion VARCHAR(2048)
url_evidencia VARCHAR(512)
registrado_por VARCHAR(256)
created_at TIMESTAMP
updated_at TIMESTAMP
```

### Tabla Actualizada: `pdm_actividades_evidencias`
**Antes:**
- `actividad_id` → FK a actividades

**Después:**
- `ejecucion_id` → FK a ejecuciones
- Todos los campos de imagen son obligatorios (NOT NULL)

## 🚀 Pasos para Ejecutar en Producción

### 1. Verificar Estado Actual
Primero verifica que el backend esté desplegado y funcionando:

```bash
curl https://tu-dominio-backend.onrender.com/api/migrations/status
```

Deberías ver un JSON con el estado de las tablas. Verifica que:
- `pdm_actividades` existe
- `pdm_actividades_ejecuciones` NO existe aún (si existe, la migración ya se ejecutó)

### 2. Obtener la Clave de Migración
La clave está definida en `backend/app/config/settings.py`:
```python
migration_secret_key: str = os.getenv("MIGRATION_SECRET_KEY", "tu-clave-secreta-2024")
```

**Si usas Render:**
1. Ve a tu servicio backend en el dashboard de Render
2. Busca en "Environment" la variable `MIGRATION_SECRET_KEY`
3. Si no existe, agrégala con un valor seguro (ej: `pdm-migration-2024-secure-key`)

### 3. Ejecutar la Migración

```bash
curl -X POST https://tu-dominio-backend.onrender.com/api/migrations/run \
  -H "X-Migration-Key: pdm-migration-2024-secure-key" \
  -H "Content-Type: application/json"
```

**Respuesta Esperada (éxito):**
```json
{
  "status": "success",
  "message": "Migraciones ejecutadas exitosamente",
  "results": [
    "✓ Tablas base creadas/verificadas",
    "✓ Tabla pdm_actividades ya existe",
    "✓ Tabla pdm_actividades_ejecuciones creada",
    "✓ Migradas X actividades a ejecuciones",
    "✓ Evidencias migradas a nueva estructura (ejecucion_id)"
  ],
  "logs": [...]
}
```

**Si hay error:**
```json
{
  "status": "error",
  "message": "Error description...",
  "results": [...],
  "logs": [...],
  "traceback": "..."
}
```

### 4. Verificar Resultado

```bash
curl https://tu-dominio-backend.onrender.com/api/migrations/status
```

Verifica que ahora muestre:
- `"pdm_actividades_ejecuciones": true`
- Record counts actualizados

### 5. Probar en la Interfaz

1. Abre el dashboard de PDM
2. Selecciona un producto con actividades
3. Haz clic en "Registrar Avance"
4. Verás:
   - Campo "Valor a Ejecutar" (nuevo)
   - Sección "Historial de Ejecuciones" (nuevo)
5. Registra una nueva ejecución con valor, descripción e imágenes
6. El historial debería mostrar la nueva ejecución con timestamp

## ⚠️ Consideraciones Importantes

### Datos Existentes
- Todas las actividades con `valor_ejecutado > 0` se migrarán automáticamente
- Se creará una ejecución por cada actividad existente
- Las evidencias existentes se asociarán a las ejecuciones migradas
- El usuario registrado será: `"Sistema - Migración"`

### Rollback
Si necesitas revertir la migración (NO RECOMENDADO en producción con datos):

```sql
-- CUIDADO: Esto eliminará todos los datos de ejecuciones
DROP TABLE IF EXISTS pdm_actividades_evidencias CASCADE;
DROP TABLE IF EXISTS pdm_actividades_ejecuciones CASCADE;

-- Recrear evidencias con estructura antigua (requiere backup)
-- (No hay forma automática de revertir sin backup)
```

### Respaldo Recomendado
Antes de ejecutar en producción, haz un backup de la base de datos:

**Si usas Render con PostgreSQL:**
```bash
pg_dump DATABASE_URL > backup_antes_migracion_ejecuciones.sql
```

O usa la función de backup automático de Render.

## 🧪 Testing Local

Para probar localmente (si tienes las tablas creadas):

```bash
# Configurar variable de entorno
export DATABASE_URL="postgresql://user:pass@localhost/dbname"

# Ejecutar migración standalone
python backend/migrate_pdm_ejecuciones.py

# O usar el endpoint
curl -X POST http://localhost:8000/api/migrations/run \
  -H "X-Migration-Key: tu-clave-local"
```

## 📊 Endpoints Afectados

### Nuevos Endpoints
- `POST /api/pdm/{slug}/actividades/{id}/ejecuciones` - Crear ejecución
- `GET /api/pdm/{slug}/actividades/{id}/ejecuciones` - Ver historial
- `DELETE /api/pdm/{slug}/actividades/{id}/ejecuciones/{id}` - Eliminar

### Endpoints Deprecados (aún funcionan)
- `POST /api/pdm/{slug}/actividades/{id}/evidencias` - Usar ejecuciones en su lugar
- `GET /api/pdm/{slug}/actividades/{id}/evidencias` - Usar historial de ejecuciones

## ✅ Verificación Post-Migración

1. **Backend Health Check:**
   ```bash
   curl https://tu-dominio-backend.onrender.com/health
   ```

2. **Verificar Tablas:**
   ```bash
   curl https://tu-dominio-backend.onrender.com/api/migrations/status | jq .
   ```

3. **Probar Endpoint de Ejecuciones:**
   ```bash
   # Listar ejecuciones de una actividad (reemplaza IDs)
   curl -H "Authorization: Bearer YOUR_TOKEN" \
     https://tu-dominio-backend.onrender.com/api/pdm/entity-slug/actividades/123/ejecuciones
   ```

4. **Verificar Frontend:**
   - Navegar al módulo PDM
   - Verificar que el historial se muestre correctamente
   - Registrar una nueva ejecución y verificar que aparezca

## 🐛 Troubleshooting

### Error: "Clave de migración inválida"
- Verifica que estás usando la clave correcta de `MIGRATION_SECRET_KEY`
- Revisa las variables de entorno en Render

### Error: "Ya hay una migración en ejecución"
- Espera a que termine la migración actual
- O consulta `/api/migrations/status` para ver el estado

### Error: "no such table: pdm_actividades"
- La migración detecta esto y se salta automáticamente
- Significa que aún no tienes datos de PDM (esperado en desarrollo)

### Frontend no muestra historial
- Verifica que el backend se haya desplegado correctamente
- Revisa la consola del navegador para errores de API
- Asegúrate de que `entitySlug` se esté pasando correctamente al diálogo

## 📞 Contacto
Si encuentras problemas durante la migración, documenta:
1. El comando ejecutado
2. La respuesta completa del servidor
3. Los logs del backend (en Render → tu servicio → Logs)
4. El resultado de `/api/migrations/status`

---

**Fecha de creación:** 5 de noviembre de 2025  
**Autor:** Sistema de Migración Automatizado  
**Versión:** 1.0  
**Commits relacionados:**
- 7a26d19: Modelos y schemas
- 71f5ffd: Endpoints backend
- 8388ce5: Frontend actualizado
- b42b190: Integración con endpoints de migración
