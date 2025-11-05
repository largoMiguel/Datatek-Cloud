# Ejemplos de Uso - Endpoints de Migraciones

## 1. Verificar Estado (Sin Autenticación)

### Con curl
```bash
curl https://pqrs-alcaldia-backend.onrender.com/api/migrations/status
```

### Con curl + formato bonito
```bash
curl -s https://pqrs-alcaldia-backend.onrender.com/api/migrations/status | python -m json.tool
```

### Respuesta Esperada
```json
{
  "status": "ok",
  "database_connected": true,
  "total_tables": 15,
  "all_tables": [
    "users",
    "entities",
    "planes_institucionales",
    "componentes_proceso",
    "actividades",
    "pdm_actividades",
    "actividades_evidencias",
    "secretarias",
    "alerts"
  ],
  "critical_tables": {
    "users": true,
    "entities": true,
    "planes_institucionales": true,
    "pdm_actividades": true,
    "secretarias": true
  },
  "record_counts": {
    "users": 5,
    "entities": 2,
    "pdm_actividades": 162,
    "planes_institucionales": 3,
    "secretarias": 8
  },
  "migration_history": {
    "running": false,
    "last_run": "2025-11-05T10:30:00",
    "last_result": "success",
    "recent_logs": [
      "[MIGRATION] === Iniciando migraciones ===",
      "[MIGRATION] Creando tablas base...",
      "[MIGRATION] === Migraciones completadas ==="
    ]
  }
}
```

## 2. Ejecutar Migraciones (Requiere Clave Secreta)

### Configurar la Clave en Render
1. Ve a Render Dashboard → Tu servicio backend → Environment
2. Agrega variable: `MIGRATION_SECRET_KEY` = `tu-clave-secreta-2024`
3. Guarda (Render redesplegará automáticamente)

### Ejecutar Migraciones
```bash
curl -X POST https://pqrs-alcaldia-backend.onrender.com/api/migrations/run \
  -H "X-Migration-Key: tu-clave-secreta-2024" \
  | python -m json.tool
```

### Respuesta Exitosa
```json
{
  "status": "success",
  "message": "Migraciones ejecutadas exitosamente",
  "results": [
    "✓ Tablas base creadas/verificadas",
    "✓ Tabla pdm_actividades ya existe",
    "✓ Columna anio_1_meta agregada",
    "✓ Columna anio_1_valor agregada",
    "✓ Tabla actividades_evidencias creada",
    "✓ Índices creados/verificados",
    "✓ Tabla planes_institucionales existe",
    "✓ Columna responsable existe en actividades",
    "✓ Tabla secretarias creada"
  ],
  "logs": [
    "[MIGRATION] === Iniciando migraciones ===",
    "[MIGRATION] Creando tablas base con SQLAlchemy...",
    "[MIGRATION] Ejecutando migraciones PDM...",
    "[MIGRATION] Agregando columna anio_1_meta...",
    "[MIGRATION] Ejecutando migraciones Planes...",
    "[MIGRATION] Ejecutando migraciones Secretarías...",
    "[MIGRATION] === Migraciones completadas ==="
  ]
}
```

## 3. Usando el Script Automático (Recomendado)

### Método Simple
```bash
# Desde el directorio backend/
./run_migration_prod.sh tu-clave-secreta-2024
```

### Con URL Personalizada
```bash
./run_migration_prod.sh tu-clave-secreta-2024 https://tu-api-custom.com
```

### Output del Script
```
=== Script de Migraciones - Producción ===

API URL: https://pqrs-alcaldia-backend.onrender.com

1. Verificando estado de la base de datos...
{
  "status": "ok",
  "database_connected": true,
  "total_tables": 15
}

2. Ejecutando migraciones...
{
  "status": "success",
  "message": "Migraciones ejecutadas exitosamente"
}

✓ Migraciones completadas exitosamente

3. Verificando estado final...
{
  "status": "ok",
  "migration_history": {
    "last_result": "success"
  }
}

=== Proceso completado ===
```

## 4. Desde JavaScript/TypeScript

### En el Frontend (Angular)
```typescript
// Verificar estado
async checkMigrationStatus() {
  const response = await fetch('https://pqrs-alcaldia-backend.onrender.com/api/migrations/status');
  const status = await response.json();
  console.log('Estado de BD:', status);
}

// Ejecutar migraciones (con clave secreta)
async runMigrations(migrationKey: string) {
  const response = await fetch('https://pqrs-alcaldia-backend.onrender.com/api/migrations/run', {
    method: 'POST',
    headers: {
      'X-Migration-Key': migrationKey
    }
  });
  const result = await response.json();
  console.log('Resultado:', result);
}
```

### Con Axios
```javascript
import axios from 'axios';

// Verificar estado
const status = await axios.get('https://pqrs-alcaldia-backend.onrender.com/api/migrations/status');
console.log(status.data);

// Ejecutar migraciones
const migrationKey = 'tu-clave-secreta-2024';
const result = await axios.post(
  'https://pqrs-alcaldia-backend.onrender.com/api/migrations/run',
  {},
  { headers: { 'X-Migration-Key': migrationKey } }
);
console.log(result.data);
```

## 5. Casos de Uso Comunes

### Verificar si la BD está lista después de un deploy
```bash
# Esperar 30 segundos y verificar
sleep 30
curl -s https://pqrs-alcaldia-backend.onrender.com/api/migrations/status | grep -q '"database_connected": true' && echo "✓ BD Lista" || echo "✗ BD No disponible"
```

### Ejecutar migraciones automáticamente después de deploy
```bash
#!/bin/bash
# Script post-deploy

echo "Esperando que Render complete el deploy..."
sleep 60

echo "Verificando estado..."
STATUS=$(curl -s https://pqrs-alcaldia-backend.onrender.com/api/migrations/status)
echo "$STATUS" | python -m json.tool

echo "Ejecutando migraciones..."
./run_migration_prod.sh tu-clave-secreta-2024

echo "Deploy completado!"
```

### Monitoreo continuo
```bash
# Verificar cada 5 minutos
watch -n 300 'curl -s https://pqrs-alcaldia-backend.onrender.com/api/migrations/status | python -m json.tool'
```

## 6. Troubleshooting por Endpoint

### Error 403: Clave Inválida
```bash
# Verificar que la clave sea correcta
curl -X POST https://pqrs-alcaldia-backend.onrender.com/api/migrations/run \
  -H "X-Migration-Key: CLAVE_INCORRECTA"

# Respuesta:
# {"detail": "Clave de migración inválida. Usa el header X-Migration-Key con la clave correcta."}

# Solución: Usar la clave configurada en MIGRATION_SECRET_KEY en Render
curl -X POST https://pqrs-alcaldia-backend.onrender.com/api/migrations/run \
  -H "X-Migration-Key: tu-clave-secreta-2024"
```

### Error 500: Already Running
```bash
# Respuesta:
# {"status": "already_running", "message": "Ya hay una migración en ejecución"}

# Solución: Esperar unos minutos y reintentar
```

## 7. Verificación Post-Migración

### Verificar tablas creadas
```bash
curl -s https://pqrs-alcaldia-backend.onrender.com/api/migrations/status \
  | python -c "import sys, json; d=json.load(sys.stdin); print('Tablas:', d['total_tables'])"
```

### Verificar registros
```bash
curl -s https://pqrs-alcaldia-backend.onrender.com/api/migrations/status \
  | python -c "import sys, json; d=json.load(sys.stdin); print('Registros:', d['record_counts'])"
```

### Verificar última ejecución
```bash
curl -s https://pqrs-alcaldia-backend.onrender.com/api/migrations/status \
  | python -c "import sys, json; d=json.load(sys.stdin); print('Última ejecución:', d['migration_history']['last_run'])"
```

## URLs de Producción

- **Status:** https://pqrs-alcaldia-backend.onrender.com/api/migrations/status
- **Run:** https://pqrs-alcaldia-backend.onrender.com/api/migrations/run
- **Login:** https://pqrs-alcaldia-backend.onrender.com/api/auth/login
- **Docs:** https://pqrs-alcaldia-backend.onrender.com/docs

## Notas Importantes

⚠️ **SEGURIDAD**
- Nunca compartas tu MIGRATION_SECRET_KEY
- Configura una clave segura y única en producción
- Usa variables de entorno para claves en scripts
- Cambia la clave si crees que fue comprometida

⚠️ **IDEMPOTENCIA**
- Las migraciones pueden ejecutarse múltiples veces
- No se perderán datos existentes
- Solo se agregan estructuras faltantes

✅ **RECOMENDACIONES**
- Siempre verifica el estado antes de ejecutar migraciones
- Haz backup antes de correr migraciones en producción
- Revisa los logs después de cada ejecución
- Usa el script automático para flujo completo
