# 📚 ÍNDICE DE DOCUMENTACIÓN - MIGRACIÓN DE BASE DE DATOS

## 🎯 Documentos Principales

### 1. **EJECUTAR_AHORA.md** ⚡ START HERE
**Ubicación:** `/EJECUTAR_AHORA.md`  
**Para:** Ejecutar la migración AHORA con comandos copy-paste  
**Contenido:**
- ✅ Comandos listos para copiar
- ✅ Paso a paso detallado
- ✅ Verificación de resultados
- ✅ Troubleshooting básico

**Úsalo si:** Quieres ejecutar la migración inmediatamente

---

### 2. **RESUMEN_MIGRACION.md** 📊 OVERVIEW
**Ubicación:** `/RESUMEN_MIGRACION.md`  
**Para:** Entender qué se implementó y por qué  
**Contenido:**
- 📦 Archivos creados/modificados
- 📊 Tablas gestionadas (15 total)
- 🔧 Problemas resueltos
- 🔐 Seguridad implementada
- 📈 Respuestas esperadas

**Úsalo si:** Quieres entender el sistema completo

---

### 3. **backend/MIGRACION_PRODUCCION.md** 📖 FULL DOCS
**Ubicación:** `/backend/MIGRACION_PRODUCCION.md`  
**Para:** Documentación técnica completa (350+ líneas)  
**Contenido:**
- 📋 Descripción detallada
- 🔐 Configuración de seguridad
- 📡 Endpoints disponibles
- 🗂️ Estructura de tablas
- 🔧 Solución de problemas
- 📊 Monitoreo post-migración
- 🎯 Casos de uso

**Úsalo si:** Necesitas información técnica profunda

---

### 4. **backend/MIGRACION_RAPIDA.md** ⚡ QUICK START
**Ubicación:** `/backend/MIGRACION_RAPIDA.md`  
**Para:** Guía rápida de 1 página  
**Contenido:**
- ⚡ Ejecución rápida (3 opciones)
- 📋 Qué hace la migración
- ⚠️ Importante
- 🆘 Solución de problemas

**Úsalo si:** Necesitas recordar comandos rápidamente

---

## 🛠️ Scripts de Ejecución

### 5. **run_migration_prod.sh** 🐚 BASH SCRIPT
**Ubicación:** `/run_migration_prod.sh`  
**Para:** Ejecutar migración con validación y confirmación  
**Uso:**
```bash
./run_migration_prod.sh https://pqrs-backend.onrender.com tu-clave-secreta-2024
```
**Características:**
- ✅ Validación paso a paso
- ✅ Confirmación requerida
- ✅ Reportes coloreados
- ✅ Verificación automática

---

### 6. **backend/run_migration_prod.py** 🐍 PYTHON SCRIPT
**Ubicación:** `/backend/run_migration_prod.py`  
**Para:** Ejecutar migración con reporting detallado  
**Uso:**
```bash
python backend/run_migration_prod.py \
  --url https://pqrs-backend.onrender.com \
  --key tu-clave-secreta-2024
```
**Características:**
- ✅ Output coloreado
- ✅ Argumentos por CLI
- ✅ Verificación pre/post migración
- ✅ Manejo de errores robusto

---

### 7. **backend/test_migration.sh** 🧪 TEST LOCAL
**Ubicación:** `/backend/test_migration.sh`  
**Para:** Probar migración en entorno local  
**Uso:**
```bash
# Primero inicia el servidor local
uvicorn app.main:app --reload

# En otra terminal
./backend/test_migration.sh
```
**Características:**
- ✅ Prueba en localhost:8000
- ✅ No afecta producción
- ✅ Validación completa

---

## 💻 Código Fuente

### 8. **backend/app/routes/migrations.py** 🔧 CORE
**Ubicación:** `/backend/app/routes/migrations.py`  
**Para:** Código fuente del sistema de migración  
**Tamaño:** 923 líneas  
**Contenido:**
- 🏗️ Funciones de migración por módulo
- 🔍 Validación de tablas/columnas
- 🔄 Conversión de ENUMs a TEXT
- 📊 Endpoints FastAPI
- 📝 Logging detallado

**Léelo si:** Quieres entender la implementación

---

## 📖 Archivos de Respaldo

### 9. **backend/app/routes/migrations_backup.py**
**Descripción:** Backup del archivo original antes de modificaciones

### 10. **backend/app/routes/migrations_v2.py**
**Descripción:** Versión intermedia durante desarrollo

---

## 🗂️ Estructura de Carpetas

```
pqrs-alcaldia/
├── EJECUTAR_AHORA.md          ⚡ START HERE
├── RESUMEN_MIGRACION.md        📊 OVERVIEW
├── MIGRACION_INDEX.md          📚 THIS FILE
├── run_migration_prod.sh       🐚 BASH SCRIPT
│
└── backend/
    ├── MIGRACION_PRODUCCION.md     📖 FULL DOCS
    ├── MIGRACION_RAPIDA.md         ⚡ QUICK START
    ├── run_migration_prod.py       🐍 PYTHON SCRIPT
    ├── test_migration.sh           🧪 TEST LOCAL
    │
    └── app/
        └── routes/
            ├── migrations.py           🔧 CORE (ACTIVO)
            ├── migrations_v2.py        📄 Version 2
            └── migrations_backup.py    💾 Backup
```

---

## 🎓 Guía de Lectura por Rol

### Para Ejecutivos/No Técnicos

1. **Lee primero:** `RESUMEN_MIGRACION.md`
2. **Ejecuta:** Copia el comando de `EJECUTAR_AHORA.md`
3. **Verifica:** Sigue el checklist de validación

### Para Desarrolladores

1. **Lee primero:** `backend/MIGRACION_PRODUCCION.md`
2. **Prueba local:** `backend/test_migration.sh`
3. **Revisa código:** `backend/app/routes/migrations.py`
4. **Ejecuta en prod:** `run_migration_prod.sh`

### Para DevOps/SysAdmins

1. **Lee primero:** `backend/MIGRACION_PRODUCCION.md` (sección de seguridad)
2. **Revisa variables:** `.env` y Render dashboard
3. **Ejecuta:** `python backend/run_migration_prod.py` (con reportes detallados)
4. **Monitorea:** Logs de Render y endpoint `/api/migrations/status`

### Para Testers/QA

1. **Lee primero:** `EJECUTAR_AHORA.md` (sección de checklist)
2. **Prueba local:** `backend/test_migration.sh`
3. **Ejecuta en staging:** Usa la URL de staging si existe
4. **Valida:** Todos los items del checklist

---

## 🔗 Enlaces Rápidos

### URLs Producción
- **Backend:** https://pqrs-backend.onrender.com
- **Frontend:** https://pqrs-frontend.onrender.com
- **Health Check:** https://pqrs-backend.onrender.com/health
- **Migration Status:** https://pqrs-backend.onrender.com/api/migrations/status

### Comandos Más Usados

**Verificar estado:**
```bash
curl https://pqrs-backend.onrender.com/api/migrations/status
```

**Ejecutar migración:**
```bash
curl -X POST https://pqrs-backend.onrender.com/api/migrations/run/status \
     -H "X-Migration-Key: tu-clave-secreta-2024"
```

**Ver completitud:**
```bash
curl https://pqrs-backend.onrender.com/api/migrations/status | \
  python -c "import sys,json; print(json.load(sys.stdin)['statistics'])"
```

---

## 📊 Tablas de Referencia

### Módulos y Tablas (15 Total)

| Módulo | Tablas | Descripción |
|--------|--------|-------------|
| **Core** | 3 | `entities`, `users`, `secretarias` |
| **PQRS** | 1 | `pqrs` |
| **Alertas** | 1 | `alerts` |
| **Planes** | 5 | `planes_institucionales`, `componentes_procesos`, `actividades`, `actividades_ejecucion`, `actividades_evidencias` |
| **PDM** | 5 | `pdm_archivos_excel`, `pdm_meta_assignments`, `pdm_avances`, `pdm_actividades`, `pdm_actividades_ejecuciones`, `pdm_actividades_evidencias` |

### Tipos ENUM Convertidos

| Tabla | Columna | Tipo Original | Tipo Nuevo |
|-------|---------|---------------|------------|
| `users` | `role` | `userrole` ENUM | `TEXT` |
| `users` | `user_type` | `usertype` ENUM | `TEXT` |
| `pqrs` | `tipo_identificacion` | `tipoidentificacion` ENUM | `VARCHAR(50)` |
| `pqrs` | `medio_respuesta` | `mediorespuesta` ENUM | `VARCHAR(50)` |
| `pqrs` | `tipo_solicitud` | `tiposolicitud` ENUM | `VARCHAR(50)` |
| `pqrs` | `estado` | `estadopqrs` ENUM | `VARCHAR(50)` |
| `planes_institucionales` | `estado` | `estadoplan` ENUM | `VARCHAR(50)` |
| `componentes_procesos` | `estado` | `estadocomponente` ENUM | `VARCHAR(50)` |

---

## 🎯 Flujo de Trabajo Recomendado

```
1. Lee RESUMEN_MIGRACION.md
   ↓
2. Verifica estado actual: curl .../api/migrations/status
   ↓
3. Ejecuta migración: Usa EJECUTAR_AHORA.md
   ↓
4. Verifica resultado: curl .../api/migrations/status
   ↓
5. Valida frontend: Prueba cada módulo
   ↓
6. Documenta warnings (si existen)
```

---

## 🆘 Soporte y Ayuda

### Preguntas Frecuentes

**P: ¿Cuántas veces puedo ejecutar la migración?**  
R: Infinitas. Es idempotente.

**P: ¿Elimina datos existentes?**  
R: No. Nunca elimina datos.

**P: ¿Cuánto tiempo toma?**  
R: Primera vez: 45-60s. Subsecuentes: 15-30s.

**P: ¿Qué pasa si falla?**  
R: Lee el traceback, ejecuta nuevamente. Es seguro.

**P: ¿Necesito backup?**  
R: Recomendado, pero la migración es no destructiva.

### Contacto

- **Issues:** Revisa logs y traceback
- **Documentación:** Este índice y documentos relacionados
- **Código:** `backend/app/routes/migrations.py`

---

## ✅ Checklist Final

Antes de ejecutar en producción:

- [ ] Leído `RESUMEN_MIGRACION.md`
- [ ] Verificado URL backend correcta
- [ ] Confirmado clave de migración
- [ ] Probado en local (opcional)
- [ ] Backup de base de datos (recomendado)

Durante la migración:

- [ ] Ejecutado comando
- [ ] Esperado 30-60 segundos
- [ ] Recibido respuesta JSON

Después de la migración:

- [ ] Verificado completitud 100%
- [ ] Probado frontend
- [ ] Documentado warnings
- [ ] Monitoreado logs

---

**Última actualización:** 5 de noviembre de 2024  
**Versión del Sistema:** 2.0  
**Estado:** ✅ Producción Ready  
**Mantenedor:** Sistema PQRS Alcaldía

---

## 🚀 ¡Empecemos!

**Próximo paso:** Lee `EJECUTAR_AHORA.md` y ejecuta el primer comando.

**Tiempo estimado total:** 5 minutos (incluyendo lectura y ejecución)

**¡Éxito!** 🎉
