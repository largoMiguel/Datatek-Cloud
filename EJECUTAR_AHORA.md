# 🚀 EJECUTAR MIGRACIÓN AHORA - PASO A PASO

## ⚡ Ejecución Inmediata (Copiar y Pegar)

### Paso 1: Verificar Estado Actual

```bash
curl https://pqrs-backend.onrender.com/api/migrations/status | python -m json.tool
```

**Qué esperar:** Ver el estado actual de las tablas y completitud.

---

### Paso 2: Ejecutar Migración Completa

```bash
curl -X POST https://pqrs-backend.onrender.com/api/migrations/run/status \
     -H "X-Migration-Key: tu-clave-secreta-2024" \
     -H "Content-Type: application/json"
```

**Tiempo estimado:** 30-60 segundos  
**Qué esperar:** JSON con resultados detallados de la migración

---

### Paso 3: Verificar Resultado

```bash
curl https://pqrs-backend.onrender.com/api/migrations/status | python -m json.tool
```

**Qué verificar:**
- `"completeness_percentage": 100.0` ✅
- `"total_tables": 15` ✅
- Todas las tablas en `true` ✅

---

## 📊 Interpretación de Resultados

### ✅ Éxito Total
```json
{
  "status": "success",
  "message": "✓ Migración completada exitosamente",
  "total_errors": 0,
  "results": [
    "✓ Tablas base creadas/verificadas",
    "✓ Tabla entities existe",
    ...
  ]
}
```
**Acción:** ¡Listo! Prueba el frontend

---

### ⚠️ Éxito con Warnings
```json
{
  "status": "success",
  "total_errors": 2,
  "errors": [
    "⚠ Índice ya existe",
    "⚠ Columna no pudo agregarse (ya existe)"
  ]
}
```
**Acción:** Normal, los warnings son seguros. Continúa.

---

### ❌ Error
```json
{
  "status": "error",
  "message": "❌ Error crítico en migración...",
  "traceback": "..."
}
```
**Acción:**
1. Lee el error en `message`
2. Revisa `traceback` para detalles
3. Contacta soporte con el traceback completo

---

## 🔍 Verificación Detallada

### Verificar Tablas Específicas

```bash
curl https://pqrs-backend.onrender.com/api/migrations/status | python -c "
import sys, json
data = json.load(sys.stdin)
tables = data.get('tables_by_module', {})
for module, module_tables in tables.items():
    print(f'\n{module.upper()}:')
    for table, exists in module_tables.items():
        status = '✅' if exists else '❌'
        print(f'  {status} {table}')
"
```

### Verificar Conteo de Registros

```bash
curl https://pqrs-backend.onrender.com/api/migrations/status | python -c "
import sys, json
data = json.load(sys.stdin)
counts = data.get('record_counts', {})
print('\nREGISTROS POR TABLA:')
for table, count in counts.items():
    print(f'  • {table}: {count}')
"
```

---

## 🎯 Checklist de Validación

Después de ejecutar la migración, verifica:

### Backend
- [ ] Endpoint `/health` responde 200
- [ ] Endpoint `/api/migrations/status` muestra 100% completitud
- [ ] No hay errores en logs de Render

### Frontend (https://pqrs-frontend.onrender.com)
- [ ] Login funciona
- [ ] Dashboard carga sin errores
- [ ] PQRS: Crear nueva PQRS
- [ ] PQRS: Listar PQRS existentes
- [ ] Planes: Ver lista de planes
- [ ] Planes: Crear nuevo plan (si aplica)
- [ ] PDM: Ver metas asignadas
- [ ] PDM: Registrar nuevo avance
- [ ] Alertas aparecen correctamente
- [ ] Usuarios: Listar y crear usuarios

---

## 🆘 Si Algo Sale Mal

### La migración no responde después de 2 minutos

```bash
# Verifica el estado
curl https://pqrs-backend.onrender.com/api/migrations/status

# Busca en la respuesta:
"running": true  # Todavía ejecutándose
"running": false # Ya terminó
```

Si `"running": false` y `"last_result": "success"`, la migración se completó.

---

### Error 403: Forbidden

**Problema:** Clave incorrecta

**Solución:**
```bash
# Asegúrate de usar la clave correcta
curl -X POST https://pqrs-backend.onrender.com/api/migrations/run/status \
     -H "X-Migration-Key: tu-clave-secreta-2024"
```

---

### Error de Conexión

**Problema:** Backend no disponible

**Solución:**
```bash
# Verifica que el backend esté corriendo
curl https://pqrs-backend.onrender.com/health

# Debería responder:
{"status":"healthy"}
```

Si no responde, verifica:
1. Render dashboard: https://dashboard.render.com
2. Logs del servicio backend
3. Estado del servicio (debería estar "Live")

---

### Completitud < 100%

**Problema:** Algunas tablas no se crearon

**Solución:**
```bash
# 1. Ver qué tablas faltan
curl https://pqrs-backend.onrender.com/api/migrations/status | grep "false"

# 2. Ejecutar migración nuevamente (es idempotente)
curl -X POST https://pqrs-backend.onrender.com/api/migrations/run/status \
     -H "X-Migration-Key: tu-clave-secreta-2024"

# 3. Verificar nuevamente
curl https://pqrs-backend.onrender.com/api/migrations/status
```

---

## 📞 Contacto y Soporte

Si necesitas ayuda:

1. **Guarda los logs:** Copia la respuesta completa de `/api/migrations/run/status`
2. **Captura errores:** Screenshot o texto de cualquier error
3. **Contexto:** Qué estabas haciendo cuando falló
4. **Información del sistema:**
   - URL del backend
   - Timestamp del error
   - Navegador usado (si aplica)

---

## ✅ Confirmación Final

Una vez completada la migración exitosamente:

```bash
# Este comando debe mostrar 100% completitud
curl https://pqrs-backend.onrender.com/api/migrations/status | \
  python -c "import sys,json; d=json.load(sys.stdin); \
  print(f\"Completitud: {d['statistics']['completeness_percentage']}%\")"
```

**Resultado esperado:** `Completitud: 100.0%`

---

## 🎉 ¡Migración Completada!

Si todo está en verde:

1. ✅ Backend funcionando
2. ✅ Migración al 100%
3. ✅ Frontend cargando
4. ✅ Funcionalidades básicas operativas

**¡Felicitaciones! El sistema está completamente migrado y listo para usar.**

---

**Última actualización:** 5 de noviembre de 2024  
**Comandos probados en:** Bash, Zsh, PowerShell (Windows)  
**URLs válidas:** https://pqrs-backend.onrender.com
