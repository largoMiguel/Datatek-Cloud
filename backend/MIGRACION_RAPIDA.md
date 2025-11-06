# 🚀 GUÍA RÁPIDA - Migración de Base de Datos en Producción

## ⚡ Ejecución Rápida

### Opción 1: Usando cURL (Recomendado)

```bash
curl -X POST https://pqrs-backend.onrender.com/api/migrations/run/status \
     -H "X-Migration-Key: tu-clave-secreta-2024"
```

### Opción 2: Usando Script Python

```bash
cd backend
python run_migration_prod.py \
  --url https://pqrs-backend.onrender.com \
  --key tu-clave-secreta-2024
```

### Opción 3: Verificar Estado Solamente

```bash
# No requiere autenticación
curl https://pqrs-backend.onrender.com/api/migrations/status | python -m json.tool
```

## 📋 Qué hace la Migración

✅ **Tablas creadas/verificadas:**
- Core: `entities`, `users`, `secretarias`
- PQRS: `pqrs`
- Alertas: `alerts`
- Planes: `planes_institucionales`, `componentes_procesos`, `actividades`, `actividades_ejecucion`, `actividades_evidencias`
- PDM: `pdm_archivos_excel`, `pdm_meta_assignments`, `pdm_avances`, `pdm_actividades`, `pdm_actividades_ejecuciones`, `pdm_actividades_evidencias`

✅ **Problemas corregidos:**
- Convierte ENUMs problemáticos a TEXT
- Agrega columnas faltantes
- Crea índices para optimización
- Mantiene integridad referencial

✅ **Seguridad:**
- Idempotente (puede ejecutarse múltiples veces)
- No elimina datos existentes
- Usa transacciones para cada operación

## ⚠️ Importante

- **Clave requerida:** `X-Migration-Key: tu-clave-secreta-2024`
- **Tiempo estimado:** 30-60 segundos
- **No interrumpir** mientras se ejecuta

## 📚 Documentación Completa

Ver archivo completo: [MIGRACION_PRODUCCION.md](./MIGRACION_PRODUCCION.md)

## 🆘 Solución de Problemas

**Error 403:** Clave incorrecta
```bash
# Usa la clave correcta configurada en MIGRATION_SECRET_KEY
```

**Ya ejecutando:** Espera unos minutos
```bash
# Verifica estado
curl https://pqrs-backend.onrender.com/api/migrations/status
```

**Error de conexión:** Verifica que el servidor esté corriendo
```bash
# Health check
curl https://pqrs-backend.onrender.com/health
```

---

**URL Backend:** https://pqrs-backend.onrender.com  
**URL Frontend:** https://pqrs-frontend.onrender.com
