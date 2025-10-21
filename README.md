# 🏛️ Sistema de Gestión PQRS - Alcaldía

Sistema web completo para la gestión de Peticiones, Quejas, Reclamos y Sugerencias (PQRS) con seguimiento de planes institucionales, análisis con IA y generación de reportes.

## 🚀 Características Principales

### 📋 Gestión de PQRS
- ✅ Creación, asignación y seguimiento de PQRS
- ✅ Estados personalizables (Pendiente, En Proceso, Resuelto, Cerrado)
- ✅ Alertas automáticas de vencimiento (15 días)
- ✅ Filtros avanzados por estado, tipo, secretaría y fechas
- ✅ Tarjetas clickeables con navegación intuitiva
- ✅ Sistema de radicados automático

### 📊 Planes Institucionales
- ✅ Gestión de planes y metas por año
- ✅ Seguimiento de avance con indicadores visuales
- ✅ Dashboard analytics con gráficos interactivos
- ✅ Alertas de metas próximas a vencer (10 días)
- ✅ Filtrado por estado y responsable
- ✅ Tarjetas clickeables para análisis rápido

### 🤖 Inteligencia Artificial
- ✅ Análisis automatizado de PQRS con OpenAI
- ✅ Análisis de planes institucionales con IA
- ✅ Recomendaciones personalizadas
- ✅ Generación de conclusiones automáticas

### 📑 Reportes PDF
- ✅ Informes completos de PQRS con gráficos
- ✅ Informes de planes institucionales
- ✅ Selección de períodos personalizados
- ✅ 13 secciones en informes de planes
- ✅ Gráficos visuales incluidos en PDF

### 👥 Gestión de Usuarios
- ✅ Roles: Administrador y Secretario
- ✅ Activación/desactivación de cuentas
- ✅ Asignación por secretarías
- ✅ Permisos basados en roles

### 🔒 Seguridad
- ✅ Autenticación JWT
- ✅ Guards de navegación
- ✅ Protección contra retroceso al login
- ✅ Interceptores HTTP automáticos
- ✅ Validación frontend y backend

## 🛠️ Tecnologías Utilizadas

### Backend
- **FastAPI** - Framework Python moderno y rápido
- **SQLAlchemy** - ORM para gestión de base de datos
- **SQLite** - Base de datos
- **JWT** - Autenticación segura
- **Uvicorn** - Servidor ASGI
- **Pydantic** - Validación de datos

### Frontend
- **Angular 20.3.0** - Framework TypeScript
- **RxJS** - Programación reactiva
- **Bootstrap 5** - Diseño responsive
- **Font Awesome** - Iconos
- **Chart.js** - Gráficos
- **jsPDF** - Generación de PDF
- **SweetAlert2** - Alertas personalizadas

## 📦 Instalación

### Requisitos Previos
- Python 3.11+
- Node.js 18+
- npm 9+

### Backend

```bash
# Navegar al directorio backend
cd backend

# Crear entorno virtual
python3.11 -m venv venv

# Activar entorno virtual
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Copiar archivo de configuración
cp .env.example .env

# Editar .env con tu API key de OpenAI
# OPENAI_API_KEY=tu-api-key-aqui

# Iniciar servidor
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

El backend estará disponible en: `http://127.0.0.1:8000`

Documentación API: `http://127.0.0.1:8000/docs`

### Frontend

```bash
# Navegar al directorio frontend
cd frontend/pqrs-frontend

# Instalar dependencias
npm install

# Iniciar servidor de desarrollo
ng serve
```

El frontend estará disponible en: `http://localhost:4200`

## 👤 Usuario por Defecto

Al iniciar la aplicación por primera vez, se crea automáticamente:

- **Usuario**: `admin`
- **Contraseña**: `admin123`
- **Rol**: Administrador

⚠️ **Importante**: Cambia la contraseña después del primer inicio de sesión.

## 🗂️ Estructura del Proyecto

```
pqrs-alcaldia/
├── backend/
│   ├── app/
│   │   ├── config/         # Configuración y base de datos
│   │   ├── models/         # Modelos SQLAlchemy
│   │   ├── routes/         # Endpoints API
│   │   ├── schemas/        # Validación Pydantic
│   │   └── utils/          # Utilidades y helpers
│   ├── requirements.txt
│   └── start.sh
├── frontend/
│   └── pqrs-frontend/
│       ├── src/
│       │   ├── app/
│       │   │   ├── components/   # Componentes Angular
│       │   │   ├── guards/       # Guards de navegación
│       │   │   ├── interceptors/ # Interceptores HTTP
│       │   │   ├── models/       # Interfaces TypeScript
│       │   │   └── services/     # Servicios Angular
│       │   └── environments/     # Configuración por entorno
│       └── package.json
└── README.md
```

## 🔧 Configuración

### Variables de Entorno - Backend

Edita `backend/.env`:

```env
# Base de datos
DATABASE_URL=sqlite:///./pqrs.db

# JWT
SECRET_KEY=tu-clave-secreta-segura-aqui
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# OpenAI API
OPENAI_API_KEY=tu-api-key-de-openai

# CORS
ALLOWED_ORIGINS=http://localhost:4200,http://127.0.0.1:4200
```

### Variables de Entorno - Frontend

Edita `frontend/pqrs-frontend/src/environments/environment.ts`:

```typescript
export const environment = {
  production: false,
  apiUrl: 'http://127.0.0.1:8000/api',
  openaiApiKey: 'tu-api-key-de-openai'
};
```

## 📖 Uso

### 1. Gestión de PQRS

1. **Crear PQRS**: Dashboard → Nueva PQRS
2. **Asignar**: Seleccionar secretario responsable
3. **Seguimiento**: Cambiar estados según avance
4. **Responder**: Agregar respuesta y marcar como resuelto
5. **Generar Informe**: Seleccionar período y descargar PDF

### 2. Planes Institucionales

1. **Crear Plan**: Planes → Nuevo Plan
2. **Agregar Metas**: Seleccionar plan → Nueva Meta
3. **Seguimiento**: Ver Analytics para gráficos y estadísticas
4. **Actualizar Avance**: Editar meta y actualizar progreso
5. **Generar Informe**: Seleccionar fechas y descargar PDF con análisis IA

### 3. Gestión de Usuarios

1. **Crear Secretario**: Dashboard → Usuarios → Nuevo Secretario
2. **Asignar Secretaría**: Seleccionar de lista predefinida
3. **Activar/Desactivar**: Cambiar estado según necesidad
4. **Eliminar**: Remover usuarios (no se puede eliminar a sí mismo)

## 🌐 API Endpoints

### Autenticación
- `POST /api/auth/login` - Iniciar sesión
- `GET /api/auth/me` - Obtener usuario actual

### PQRS
- `GET /api/pqrs/` - Listar PQRS
- `POST /api/pqrs/` - Crear PQRS
- `GET /api/pqrs/{id}` - Obtener PQRS
- `PUT /api/pqrs/{id}` - Actualizar PQRS
- `DELETE /api/pqrs/{id}` - Eliminar PQRS

### Planes
- `GET /api/planes/` - Listar planes
- `POST /api/planes/` - Crear plan
- `GET /api/planes/{id}` - Obtener plan
- `PUT /api/planes/{id}` - Actualizar plan
- `DELETE /api/planes/{id}` - Eliminar plan
- `GET /api/planes/{id}/metas/` - Listar metas
- `POST /api/planes/{id}/metas/` - Crear meta

### Usuarios
- `GET /api/users/` - Listar usuarios
- `POST /api/users/` - Crear usuario
- `PATCH /api/users/{id}/toggle-status` - Activar/desactivar
- `DELETE /api/users/{id}` - Eliminar usuario

Documentación completa: `http://127.0.0.1:8000/docs`

## 📄 Licencia

Este proyecto es de uso privado para la Alcaldía.

## 👨‍💻 Autor

Desarrollado con ❤️ para la gestión eficiente de PQRS

---

⭐ Si este proyecto te fue útil, considera darle una estrella en GitHub!
