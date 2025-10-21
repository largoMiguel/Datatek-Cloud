# Sistema de Gestión PQRS - Alcaldía

Sistema completo para la gestión de Peticiones, Quejas, Reclamos y Sugerencias (PQRS) de una alcaldía.

## Arquitectura

- **Backend**: Python + FastAPI + SQLAlchemy + PostgreSQL/SQLite
- **Frontend**: Angular + Bootstrap/Angular Material
- **Autenticación**: JWT tokens
- **Base de datos**: PostgreSQL (producción) / SQLite (desarrollo)

## Funcionalidades

### Roles de Usuario
- **Administrador**: Gestiona usuarios y asigna PQRS
- **Secretario**: Crea y gestiona sus PQRS asignadas

### Gestión de PQRS
- Creación automática con asignación al secretario creador
- Campos: Usuario, Tipo de solicitud, Fecha de solicitud, Fecha de cierre, Fecha de delegación, Estado
- Workflow de estados: Pendiente → En proceso → Resuelto → Cerrado
- Asignación manual por administrador

## Estructura del Proyecto

```
pqrs-alcaldia/
├── backend/          # API FastAPI
│   ├── app/
│   ├── models/
│   ├── routes/
│   ├── config/
│   └── requirements.txt
├── frontend/         # Aplicación Angular
│   ├── src/
│   ├── angular.json
│   └── package.json
└── README.md
```

## Instalación y Ejecución

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
ng serve
```

## API Endpoints

- `POST /auth/login` - Autenticación
- `POST /auth/register` - Registro (solo admin)
- `GET /pqrs/` - Listar PQRS
- `POST /pqrs/` - Crear PQRS
- `PUT /pqrs/{id}` - Actualizar PQRS
- `DELETE /pqrs/{id}` - Eliminar PQRS
- `POST /pqrs/{id}/assign` - Asignar PQRS (admin)

## Estados de PQRS

1. **Pendiente**: Recién creada
2. **En Proceso**: Siendo trabajada
3. **Resuelto**: Completada, pendiente de cierre
4. **Cerrado**: Finalizada