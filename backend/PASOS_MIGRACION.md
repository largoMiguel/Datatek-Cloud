# 🚀 Pasos para Ejecutar Migraciones en Producción

## Método Simple con Clave Secreta

### Paso 1: Configurar la Clave en Render ⚙️

1. Ve a tu proyecto en [Render Dashboard](https://dashboard.render.com)
2. Selecciona tu servicio backend
3. Ve a **Environment** → **Environment Variables**
4. Agrega una nueva variable:
   - **Key:** `MIGRATION_SECRET_KEY`
   - **Value:** `tu-clave-secreta-2024` (o la que prefieras)
5. Guarda los cambios (Render redesplegará automáticamente)

### Paso 2: Ejecutar Migraciones 🎯

#### Opción A: Con el Script Automático (Recomendado)

```bash
cd backend
./run_migration_prod.sh tu-clave-secreta-2024
```

#### Opción B: Con curl Directo

```bash
# 1. Verificar estado (sin clave)
curl https://pqrs-alcaldia-backend.onrender.com/api/migrations/status

# 2. Ejecutar migraciones (con clave)
curl -X POST https://pqrs-alcaldia-backend.onrender.com/api/migrations/run \
  -H "X-Migration-Key: tu-clave-secreta-2024"
```

### Paso 3: Verificar Resultado ✅

```bash
# Ver el estado final
curl https://pqrs-alcaldia-backend.onrender.com/api/migrations/status
```

---

## 📋 Ejemplo Completo Paso a Paso

```bash
# 1. Verificar que la API está funcionando
curl https://pqrs-alcaldia-backend.onrender.com/health

# 2. Ver estado de la base de datos
curl https://pqrs-alcaldia-backend.onrender.com/api/migrations/status | python -m json.tool

# 3. Ejecutar migraciones con tu clave
curl -X POST https://pqrs-alcaldia-backend.onrender.com/api/migrations/run \
  -H "X-Migration-Key: tu-clave-secreta-2024" \
  | python -m json.tool

# 4. Confirmar que todo funcionó
curl https://pqrs-alcaldia-backend.onrender.com/api/migrations/status | python -m json.tool
```

---

## 🔐 Variables de Entorno Requeridas en Render

Asegúrate de tener estas variables configuradas:

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `DATABASE_URL` | URL de PostgreSQL | `postgresql://user:pass@host:5432/db` |
| `MIGRATION_SECRET_KEY` | Clave para ejecutar migraciones | `tu-clave-secreta-2024` |
| `SECRET_KEY` | Clave para JWT | `otra-clave-diferente` |

---

## ❌ Problemas Comunes

### Error: "Clave de migración inválida"
**Causa:** La clave en el header no coincide con `MIGRATION_SECRET_KEY` en Render

**Solución:**
```bash
# Verifica que uses la misma clave que configuraste en Render
curl -X POST https://pqrs-alcaldia-backend.onrender.com/api/migrations/run \
  -H "X-Migration-Key: LA_CLAVE_CORRECTA"
```

### Error: "Connection refused"
**Causa:** La API no está disponible o Render está redesplegando

**Solución:**
- Espera 2-3 minutos después de hacer push
- Verifica en Render Dashboard que el deploy terminó
- Prueba el endpoint `/health` primero

### Error: "Already running"
**Causa:** Ya hay una migración en ejecución

**Solución:**
- Espera 2-3 minutos
- Verifica el estado con `/api/migrations/status`
- Si persiste, contacta al administrador

---

## 🎯 Resumen de Comandos Rápidos

```bash
# Método más simple (todo en uno)
cd /Users/largo/Documents/SOLUCTIONS/pqrs-alcaldia/backend
./run_migration_prod.sh tu-clave-secreta-2024

# O si prefieres curl directo
curl -X POST https://pqrs-alcaldia-backend.onrender.com/api/migrations/run \
  -H "X-Migration-Key: tu-clave-secreta-2024"
```

---

## ✨ Características

- ✅ **No requiere autenticación de usuario** - Solo necesitas la clave secreta
- ✅ **Idempotente** - Puedes ejecutar múltiples veces sin problemas
- ✅ **Sin pérdida de datos** - Solo crea/modifica estructura, no elimina datos
- ✅ **Logs detallados** - Cada operación se registra
- ✅ **Verificación de estado** - Endpoint público para monitoreo

---

## 📞 Soporte

Si algo sale mal:

1. Verifica el estado: `curl .../api/migrations/status`
2. Revisa los logs en Render Dashboard
3. Confirma que `MIGRATION_SECRET_KEY` está configurada
4. Asegúrate de que el backend terminó de desplegar
