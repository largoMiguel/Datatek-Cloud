# Fix Urgente: Normalización de user_type

## Problema
Error al hacer login o consultar usuarios:
```
LookupError: 'CONTRATISTA' is not among the defined enum values. 
Enum name: usertype. Possible values: secretario, contratista
```

**Causa**: La base de datos tiene valores en MAYÚSCULAS ('CONTRATISTA', 'SECRETARIO') pero el enum de SQLAlchemy espera minúsculas ('contratista', 'secretario').

## Solución

### Opción 1: Via API de Migraciones (RECOMENDADO para producción)

```bash
# 1. Ejecutar migración que incluye normalización automática
curl -X POST https://pqrs-backend.onrender.com/api/migrations/run \
  -H "X-Migration-Key: tu-clave-secreta-2024"

# 2. Verificar que se aplicó correctamente
curl -X GET https://pqrs-backend.onrender.com/api/migrations/status \
  -H "X-Migration-Key: tu-clave-secreta-2024"
```

**Respuesta esperada**:
```json
{
  "status": "success",
  "migrations": [
    "✅ Conexión a base de datos verificada",
    "ℹ️ Columna 'user_type' ya existe en users",
    "ℹ️ Columna 'allowed_modules' ya existe en users",
    "🔧 Normalizados 3 registros: user_type a minúsculas"
  ]
}
```

### Opción 2: Script Local (para desarrollo)

```bash
cd backend
python normalize_user_type.py
```

**Salida esperada**:
```
🔄 Iniciando normalización de user_type...
   Base de datos: localhost/pqrs_db

📊 Encontrados 3 registros con user_type en mayúsculas
✅ Normalización completada:
   - 1 SECRETARIO → secretario
   - 2 CONTRATISTA → contratista
   - Total: 3 registros actualizados

✨ Proceso completado
```

## Qué hace la migración

1. **Detecta** registros con `user_type` en MAYÚSCULAS
2. **Normaliza** a minúsculas:
   - `SECRETARIO` → `secretario`
   - `CONTRATISTA` → `contratista`
3. **Valida** que no queden valores incorrectos

## Verificación Post-Migración

### Verificar en Base de Datos (PostgreSQL)
```sql
-- Ver distribución de user_type
SELECT user_type, COUNT(*) 
FROM users 
WHERE user_type IS NOT NULL 
GROUP BY user_type;

-- Resultado esperado:
-- user_type    | count
-- -------------|------
-- secretario   |   1
-- contratista  |   2
```

### Probar Login
1. Intenta hacer login con un usuario contratista
2. Verifica que no aparezca el error de enum
3. Confirma que la barra muestra "Contratista" correctamente

## Archivos Modificados

### Backend
- `backend/app/routes/migrations.py`: 
  - Agregado paso 5: normalización de `user_type`
  - Ejecuta UPDATE automático en `POST /api/migrations/run`

- `backend/normalize_user_type.py`: 
  - Script standalone para normalización
  - Útil para desarrollo local

- `backend/app/models/user.py`:
  - `user_type` Column usa `values_callable` con `.value` (minúsculas)

- `backend/app/routes/users.py`:
  - Normalización en `create_user()` y `update_user()`
  - Valida y convierte a minúsculas antes de guardar

## Para Producción (Render)

### Pasos de Ejecución
1. **Verificar deploy**: Asegurar que el código más reciente está desplegado
2. **Ejecutar migración**:
   ```bash
   curl -X POST https://pqrs-backend.onrender.com/api/migrations/run \
     -H "X-Migration-Key: tu-clave-secreta-2024"
   ```
3. **Verificar status**:
   ```bash
   curl -X GET https://pqrs-backend.onrender.com/api/migrations/status \
     -H "X-Migration-Key: tu-clave-secreta-2024"
   ```
4. **Probar login**: Con usuario contratista

### Rollback (si es necesario)
Si algo falla, puedes revertir manualmente:
```sql
-- Solo si necesitas revertir (NO RECOMENDADO)
UPDATE users SET user_type = 'CONTRATISTA' WHERE user_type = 'contratista';
UPDATE users SET user_type = 'SECRETARIO' WHERE user_type = 'secretario';
```

## Prevención Futura

Los siguientes cambios ya aplicados previenen este problema:

✅ **Backend valida y normaliza** en create/update  
✅ **Modelo SQLAlchemy** usa `values_callable` con minúsculas  
✅ **Migración automática** normaliza datos existentes  
✅ **Frontend** envía valores correctos desde el formulario  

## Checklist de Deployment

- [ ] Código en master (commits aplicados)
- [ ] Render desplegó la última versión
- [ ] Ejecutar `POST /api/migrations/run`
- [ ] Verificar normalización con `GET /api/migrations/status`
- [ ] Probar login de usuario contratista
- [ ] Verificar que barra muestra "Contratista"
- [ ] Probar creación de nuevo usuario (debe guardar en minúsculas)

---

**Fecha de fix**: 29 de octubre de 2025  
**Commits relacionados**:
- `502801a`: Alinea Enum user_type a valores en minúsculas
- `ff8494a`: Normaliza user_type en create/update
- `959defe`: Muestra 'Contratista' en barra UI
- `[NUEVO]`: Agrega normalización a endpoint de migraciones
