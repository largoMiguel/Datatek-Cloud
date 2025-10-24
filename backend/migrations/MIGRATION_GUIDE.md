# Migración de Base de Datos PostgreSQL en Render

## Problema
La base de datos PostgreSQL en producción (Render) no tiene las columnas `cedula`, `telefono` y `direccion` en la tabla `users`, causando el error:
```
psycopg2.errors.UndefinedColumn) column users.cedula does not exist
```

## Solución

Existen 3 métodos para ejecutar la migración:

---

## Método 1: Ejecutar script Python desde Shell de Render (RECOMENDADO)

### Pasos:

1. **Acceder al Shell de Render:**
   - Ve a tu servicio backend en Render Dashboard
   - Click en "Shell" en el menú lateral
   - Esto abrirá una terminal en el servidor

2. **Ejecutar el script de migración:**
   ```bash
   cd /opt/render/project/src/backend/migrations
   python3 migrate_postgres.py
   ```

3. **Verificar el resultado:**
   - El script mostrará el progreso de cada paso
   - Al final mostrará la estructura completa de la tabla `users`
   - Busca el mensaje: `✅ ¡Migración completada exitosamente!`

---

## Método 2: Usar PostgreSQL Shell de Render

### Pasos:

1. **Acceder al Dashboard de Render:**
   - Ve a tu base de datos PostgreSQL en Render
   - Click en "Connect" → "External Connection"
   - Copia las credenciales (PSQL Command)

2. **Conectarte desde tu terminal local:**
   ```bash
   # Usa el comando PSQL que copiaste, algo como:
   PGPASSWORD=tu_password psql -h tu-host.oregon-postgres.render.com -U tu_usuario tu_database
   ```

3. **Ejecutar el script SQL:**
   ```sql
   -- Copiar y pegar el contenido de add_ciudadano_fields_postgres.sql
   -- O ejecutar:
   \i /ruta/a/add_ciudadano_fields_postgres.sql
   ```

---

## Método 3: Usar el Dashboard de Render (Más Simple)

### Pasos:

1. **Acceder a la base de datos:**
   - Ve a tu PostgreSQL database en Render Dashboard
   - Click en "Connect" → "External Connection"
   - Usa un cliente PostgreSQL (como pgAdmin, DBeaver, o TablePlus)

2. **Conectarte con las credenciales:**
   - Host: [tu-host].oregon-postgres.render.com
   - Port: 5432
   - Database: [tu-database-name]
   - Username: [tu-username]
   - Password: [tu-password]

3. **Ejecutar las siguientes consultas SQL:**

   ```sql
   -- 1. Agregar el valor 'CIUDADANO' al ENUM
   DO $$
   BEGIN
       IF NOT EXISTS (
           SELECT 1
           FROM pg_enum
           WHERE enumlabel = 'CIUDADANO'
           AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'userrole')
       ) THEN
           ALTER TYPE userrole ADD VALUE 'CIUDADANO';
       END IF;
   END$$;

   -- 2. Agregar las nuevas columnas
   ALTER TABLE users ADD COLUMN IF NOT EXISTS cedula VARCHAR(20);
   ALTER TABLE users ADD COLUMN IF NOT EXISTS telefono VARCHAR(20);
   ALTER TABLE users ADD COLUMN IF NOT EXISTS direccion VARCHAR(255);

   -- 3. Crear índice
   CREATE INDEX IF NOT EXISTS idx_users_cedula ON users(cedula);

   -- 4. Verificar
   SELECT column_name, data_type, character_maximum_length
   FROM information_schema.columns
   WHERE table_name = 'users'
   ORDER BY ordinal_position;
   ```

---

## Verificación Post-Migración

Después de ejecutar la migración, verifica que funcione:

1. **Reiniciar el servicio en Render:**
   - Ve a tu servicio backend
   - Click en "Manual Deploy" → "Clear build cache & deploy"

2. **Probar el endpoint de registro ciudadano:**
   ```bash
   curl -X POST https://pqrs-backend.onrender.com/api/auth/register-ciudadano \
     -H "Content-Type: application/json" \
     -d '{
       "username": "test_ciudadano",
       "password": "test123",
       "email": "test@example.com",
       "full_name": "Test Ciudadano",
       "cedula": "1234567890",
       "telefono": "3001234567",
       "direccion": "Calle 123",
       "role": "ciudadano"
     }'
   ```

3. **Verificar los logs:**
   - Los errores `column users.cedula does not exist` deben desaparecer
   - El servicio debe iniciar sin errores de base de datos

---

## Troubleshooting

### Si el valor ENUM no se agrega:
```sql
-- Verificar valores actuales del ENUM
SELECT enumlabel 
FROM pg_enum 
WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'userrole');

-- Si falla, crear el enum manualmente en una transacción separada
BEGIN;
ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'CIUDADANO';
COMMIT;
```

### Si las columnas ya existen:
El script usa `IF NOT EXISTS`, por lo que es seguro ejecutarlo múltiples veces.

### Si hay errores de permisos:
Asegúrate de estar usando el usuario principal de la base de datos (no read-only).

---

## Archivos de Migración

- `add_ciudadano_fields_postgres.sql` - Script SQL directo
- `migrate_postgres.py` - Script Python automatizado
- Este archivo (MIGRATION_GUIDE.md) - Guía completa

---

## Notas Importantes

⚠️ **IMPORTANTE:** 
- La operación `ALTER TYPE ADD VALUE` en PostgreSQL **NO puede ejecutarse dentro de una transacción**.
- Si usas un cliente SQL, asegúrate de ejecutar el ALTER TYPE en una consulta separada.
- El script Python maneja esto automáticamente usando `AUTOCOMMIT`.

✅ **Seguridad:**
- Todas las operaciones usan `IF NOT EXISTS`
- Es seguro ejecutar el script múltiples veces
- No se perderán datos existentes

🔄 **Orden de Ejecución:**
1. Agregar valor al ENUM (requiere AUTOCOMMIT)
2. Agregar columnas (puede estar en transacción)
3. Crear índices (puede estar en transacción)
4. Agregar comentarios (opcional)
