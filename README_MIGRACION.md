# 🚀 MIGRACIÓN DE BASE DE DATOS - INICIO RÁPIDO

## ⚡ EJECUTAR AHORA (Método Más Rápido)

```bash
./EJECUTAR_MIGRACION_PRODUCCION.sh
```

Este script ejecuta todo automáticamente con validación y reportes.

---

## 📋 Alternativas de Ejecución

### Opción 1: cURL Simple
```bash
curl -X POST https://pqrs-backend.onrender.com/api/migrations/run/status \
     -H "X-Migration-Key: tu-clave-secreta-2024"
```

### Opción 2: Script Bash
```bash
./run_migration_prod.sh https://pqrs-backend.onrender.com tu-clave-secreta-2024
```

### Opción 3: Script Python
```bash
python backend/run_migration_prod.py \
  --url https://pqrs-backend.onrender.com \
  --key tu-clave-secreta-2024
```

---

## 📚 Documentación Completa

| Documento | Descripción | Cuándo Usarlo |
|-----------|-------------|---------------|
| **[EJECUTAR_AHORA.md](EJECUTAR_AHORA.md)** | Comandos paso a paso | Ejecutar migración inmediatamente |
| **[RESUMEN_MIGRACION.md](RESUMEN_MIGRACION.md)** | Resumen ejecutivo | Entender qué se implementó |
| **[MIGRACION_INDEX.md](MIGRACION_INDEX.md)** | Índice completo | Navegar toda la documentación |
| **[backend/MIGRACION_PRODUCCION.md](backend/MIGRACION_PRODUCCION.md)** | Docs técnicas (350+ líneas) | Información técnica profunda |
| **[backend/MIGRACION_RAPIDA.md](backend/MIGRACION_RAPIDA.md)** | Guía rápida (1 página) | Recordar comandos rápidamente |

---

## ✅ Verificación Rápida

### Ver Estado Actual
```bash
curl https://pqrs-backend.onrender.com/api/migrations/status
```

### Ver Solo Completitud
```bash
curl https://pqrs-backend.onrender.com/api/migrations/status | \
  python -c "import sys,json; d=json.load(sys.stdin); \
  print(f\"Completitud: {d['statistics']['completeness_percentage']}%\")"
```

---

## 📊 Qué Hace la Migración

✅ **Crea/Verifica 15 Tablas:**
- Core (3): `entities`, `users`, `secretarias`
- PQRS (1): `pqrs`
- Alertas (1): `alerts`
- Planes (5): `planes_institucionales`, `componentes_procesos`, `actividades`, `actividades_ejecucion`, `actividades_evidencias`
- PDM (5): `pdm_archivos_excel`, `pdm_meta_assignments`, `pdm_avances`, `pdm_actividades`, `pdm_actividades_ejecuciones`, `pdm_actividades_evidencias`

✅ **Soluciona Problemas:**
- Convierte ENUMs a TEXT
- Agrega columnas faltantes
- Crea índices
- Mantiene integridad referencial

✅ **100% Seguro:**
- Idempotente (ejecutar múltiples veces)
- No elimina datos
- Usa transacciones

---

## ⏱️ Tiempo Estimado

- Primera ejecución: **45-60 segundos**
- Ejecuciones subsecuentes: **15-30 segundos**
- Verificación de estado: **< 2 segundos**

---

## 🔐 Configuración

### Variables de Entorno Requeridas

En Render o `.env`:
```bash
DATABASE_URL=postgresql://user:password@host/database
MIGRATION_SECRET_KEY=tu-clave-secreta-2024
```

---

## 🆘 Solución Rápida de Problemas

### Error 403
**Problema:** Clave incorrecta  
**Solución:** Verifica que uses `tu-clave-secreta-2024`

### Error de Conexión
**Problema:** Backend no disponible  
**Solución:** Verifica en https://dashboard.render.com

### Completitud < 100%
**Problema:** Tablas faltantes  
**Solución:** Ejecuta migración nuevamente (es idempotente)

---

## 🎯 Checklist Post-Migración

- [ ] Verificar completitud 100%
- [ ] Probar login en frontend
- [ ] Crear y listar PQRS
- [ ] Ver planes institucionales
- [ ] Registrar avance en PDM
- [ ] Verificar alertas
- [ ] Revisar logs si hay warnings

---

## 📞 Soporte

**URLs:**
- Backend: https://pqrs-backend.onrender.com
- Frontend: https://pqrs-frontend.onrender.com

**Documentación:**
- Ver [MIGRACION_INDEX.md](MIGRACION_INDEX.md) para índice completo

**Logs:**
- Render Dashboard → Servicio backend → Logs

---

## 🎉 ¡Listo!

Ejecuta el script principal y sigue las instrucciones:

```bash
./EJECUTAR_MIGRACION_PRODUCCION.sh
```

**Tiempo total estimado:** 5 minutos (incluyendo validación)

---

**Fecha:** 5 de noviembre de 2024  
**Versión:** 2.0  
**Estado:** ✅ Producción Ready
