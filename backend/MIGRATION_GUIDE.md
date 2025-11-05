# Guía de Migraciones de Base de Datos

## Endpoints Disponibles

### 1. Verificar Estado de la Base de Datos
```bash
curl https://pqrs-alcaldia-backend.onrender.com/api/migrations/status
```

Este endpoint:
- ✅ No requiere autenticación
- Retorna el estado de todas las tablas
- Muestra conteos de registros
- Indica si hay migraciones pendientes

**Respuesta ejemplo:**
```json
{
  "status": "ok",
  "database_connected": true,
  "total_tables": 15,
  "critical_tables": {
    "users": true,
    "entities": true,
    "pdm_actividades": true,
    "planes_institucionales": true
  },
  "record_counts": {
    "users": 5,
    "entities": 2,
    "pdm_actividades": 162
  }
}
```

### 2. Ejecutar Migraciones
```bash
curl -X POST https://pqrs-alcaldia-backend.onrender.com/api/migrations/run \
  -H "Authorization: Bearer YOUR_SUPERADMIN_TOKEN" \
  -H "Content-Type: application/json"
```

Este endpoint:
- 🔒 Requiere autenticación con token de SUPERADMIN
- Ejecuta todas las migraciones pendientes
- Crea tablas faltantes
- Agrega columnas nuevas
- Retorna log detallado de cada operación

**Respuesta ejemplo:**
```json
{
  "status": "success",
  "message": "Migraciones ejecutadas exitosamente",
  "results": [
    "✓ Tablas base creadas/verificadas",
    "✓ Tabla pdm_actividades creada",
    "✓ Columna anio_1_meta agregada",
    "✓ Tabla actividades_evidencias creada"
  ],
  "logs": [
    "[MIGRATION] === Iniciando migraciones ===",
    "[MIGRATION] Ejecutando migraciones PDM..."
  ]
}
```

## Obtener Token de SUPERADMIN

### Método 1: Login via API
```bash
curl -X POST https://pqrs-alcaldia-backend.onrender.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@tudominio.com",
    "password": "tu_password"
  }'
```

### Método 2: Desde el Frontend
1. Ingresa al sistema como SUPERADMIN
2. Abre las DevTools (F12)
3. Ve a Application > Local Storage
4. Busca la clave `authToken`
5. Copia el valor del token

## Script Automático (Recomendado)

Usa el script `run_migration_prod.sh` para ejecutar todas las migraciones:

```bash
# Dar permisos de ejecución
chmod +x run_migration_prod.sh

# Ejecutar con tu token
./run_migration_prod.sh YOUR_SUPERADMIN_TOKEN

# O especificar URL personalizada
./run_migration_prod.sh YOUR_TOKEN https://tu-api-custom.com
```

## Migraciones Incluidas

### PDM (Plan de Desarrollo Municipal)
- ✓ Tabla `pdm_actividades`
- ✓ Columnas de programación anual (anio_1_meta, anio_1_valor, etc.)
- ✓ Tabla `actividades_evidencias`
- ✓ Índices para optimización

### Planes Institucionales
- ✓ Tabla `planes_institucionales`
- ✓ Tabla `componentes_proceso`
- ✓ Tabla `actividades`
- ✓ Tabla `actividades_ejecucion`
- ✓ Columna `responsable` en actividades

### Secretarías
- ✓ Tabla `secretarias`
- ✓ Relación con entities
- ✓ Índices de búsqueda

### Alertas
- ✓ Tabla `alerts`
- ✓ Tipos de alerta
- ✓ Estados de lectura

## Troubleshooting

### Error: "Solo SUPERADMIN puede ejecutar migraciones"
**Causa:** El token proporcionado no es de un usuario SUPERADMIN.
**Solución:** Verifica que estés usando el token correcto de un SUPERADMIN.

### Error: "Ya hay una migración en ejecución"
**Causa:** Otra migración está corriendo o quedó bloqueada.
**Solución:** Espera unos minutos y vuelve a intentar. Si persiste, verifica el endpoint `/status`.

### Error de conexión a la base de datos
**Causa:** Problemas de conectividad o configuración.
**Solución:** 
1. Verifica que la variable `DATABASE_URL` esté configurada en Render
2. Verifica que la base de datos PostgreSQL esté activa
3. Revisa los logs de Render

## Flujo Recomendado para Producción

1. **Pre-deployment:** Hacer backup de la base de datos
   ```bash
   # En Render, usa su interfaz de backup
   # O con pg_dump si tienes acceso directo
   ```

2. **Deploy:** Push a GitHub (ya hecho)
   ```bash
   git push origin master
   ```

3. **Esperar:** Que Render complete el build (~2-5 minutos)

4. **Verificar estado:** Sin autenticación
   ```bash
   curl https://pqrs-alcaldia-backend.onrender.com/api/migrations/status
   ```

5. **Ejecutar migraciones:** Con token SUPERADMIN
   ```bash
   ./run_migration_prod.sh YOUR_TOKEN
   ```

6. **Validar:** Verificar que todo funciona correctamente
   - Revisar logs en Render
   - Probar funcionalidades críticas
   - Verificar conteos en `/api/migrations/status`

## Rollback

Si algo sale mal y necesitas revertir:

1. **Via Render:** Usa la opción "Rollback" en el dashboard
2. **Via Git:** Revertir el commit y hacer push
   ```bash
   git revert HEAD
   git push origin master
   ```

## Notas Importantes

- ⚠️ Las migraciones son **idempotentes**: puedes ejecutarlas múltiples veces sin problemas
- ⚠️ Las migraciones **no eliminan** datos existentes, solo agregan estructuras
- ⚠️ Siempre haz **backup** antes de ejecutar migraciones en producción
- ✅ El endpoint `/status` es público para facilitar debugging
- ✅ El endpoint `/run` requiere SUPERADMIN para seguridad
