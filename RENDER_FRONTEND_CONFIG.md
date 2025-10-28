# 🚀 Configuración del Frontend en Render

## ⚠️ CAMBIO IMPORTANTE: De Static Site a Web Service

El frontend **debe ser un Web Service** (no Static Site) para que funcione correctamente el routing de Angular.

---

## 📋 Configuración en Render Dashboard

### 1. Tipo de Servicio
- **Service Type**: `Web Service` (NO Static Site)

### 2. Build & Deploy Settings

#### Root Directory
```
frontend/pqrs-frontend
```

#### Build Command
```bash
npm install && npm run build:prod
```

#### Start Command
```bash
node server.js
```

### 3. Variables de Entorno

No se requieren variables especiales para el frontend, pero asegúrate de que el backend tenga configurado CORS correctamente con la URL del frontend:

```
ALLOWED_ORIGINS=https://pqrs-frontend.onrender.com,http://localhost:4200
```

---

## 🔧 Cómo funciona

1. **Build**: Angular compila la app a `dist/pqrs-frontend/browser`
2. **Server**: Express (server.js) sirve los archivos estáticos
3. **Fallback SPA**: Cualquier ruta que no sea archivo estático devuelve `index.html`
4. **Angular Router**: Toma el control y renderiza el componente correcto

---

## ✅ Verificación

Después del deploy, prueba estas URLs (todas deben funcionar sin 404):

- https://pqrs-frontend.onrender.com/
- https://pqrs-frontend.onrender.com/sora-boyaca
- https://pqrs-frontend.onrender.com/sora-boyaca/login
- https://pqrs-frontend.onrender.com/soft-admin

Recarga la página (F5) en cualquiera de estas URLs y debe seguir funcionando.

---

## 🐛 Troubleshooting

### Si ves 404 en rutas:
1. Verifica que el servicio sea **Web Service** (no Static Site)
2. Verifica que el Start Command sea `node server.js`
3. Revisa los logs: debe decir `[server] Serving static from: ...`

### Si la app no carga:
1. Verifica que el Build Command termine exitosamente
2. Verifica que exista `dist/pqrs-frontend/browser/index.html` después del build
3. Verifica que Express esté en las dependencias (`package.json`)

---

## 📦 Archivos Clave

- `server.js`: Servidor Express que sirve la app
- `Procfile`: Define el comando de inicio (web: node server.js)
- `package.json`: Scripts de build y start
- `build.sh`: Script auxiliar de build (opcional)
