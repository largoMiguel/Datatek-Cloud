# Configuración de Variables de Entorno en Render

## 🔧 Variables Requeridas

Para que el backend funcione correctamente en Render, debes configurar las siguientes variables de entorno:

### 1. ALLOWED_ORIGINS (CRÍTICO para CORS)
```
ALLOWED_ORIGINS=https://pqrs-frontend.onrender.com,http://localhost:4200
```

### 2. DATABASE_URL
```
DATABASE_URL=postgresql://usuario:password@host/database
```

### 3. SECRET_KEY
```
SECRET_KEY=tu-clave-secreta-super-segura-cambiar-en-produccion
```

### 4. ENVIRONMENT
```
ENVIRONMENT=production
```

### 5. DEBUG (opcional)
```
DEBUG=false
```

### 6. OPENAI_API_KEY (opcional, para IA)
```
OPENAI_API_KEY=sk-...
```

---

## 📋 Pasos para Configurar en Render

1. Ve al Dashboard de Render
2. Selecciona tu servicio **pqrs-backend**
3. Ve a la pestaña **Environment**
4. Agrega cada variable con el botón **Add Environment Variable**
5. Guarda los cambios
6. El servicio se reiniciará automáticamente

---

## ⚠️ Solución al Error CORS

El error:
```
Access to XMLHttpRequest at 'https://pqrs-backend.onrender.com/api/pqrs/' 
from origin 'https://pqrs-frontend.onrender.com' has been blocked by CORS policy
```

**Se soluciona configurando correctamente la variable `ALLOWED_ORIGINS`.**

### Verificación:
1. Asegúrate de que `ALLOWED_ORIGINS` contenga **exactamente** la URL de tu frontend
2. **NO** incluyas barra final: ❌ `https://pqrs-frontend.onrender.com/`
3. **SÍ** usa el formato correcto: ✅ `https://pqrs-frontend.onrender.com`

---

## 🔍 Debug

Para verificar que las variables están configuradas correctamente, revisa los logs del backend en Render.

Deberías ver al inicio:
```
🌐 CORS Origins configurados: ['https://pqrs-frontend.onrender.com', 'http://localhost:4200']
   Allowed Origins String: https://pqrs-frontend.onrender.com,http://localhost:4200
```

Si ves algo diferente, revisa las variables de entorno.

---

## 🚨 Error 500 Internal Server Error

El error 500 generalmente indica un problema en el servidor, no solo CORS. Los cambios realizados:

1. ✅ **Middleware de captura de errores**: Ahora todos los errores 500 incluyen headers CORS
2. ✅ **Mejor logging**: Los errores se registran con traceback completo
3. ✅ **Try-catch en creación de PQRS**: Manejo de errores más robusto

### Para diagnosticar error 500:
1. Ve a los logs de Render
2. Busca líneas que empiecen con `❌ Error`
3. Revisa el traceback completo
4. Verifica que la base de datos esté correctamente migrada
