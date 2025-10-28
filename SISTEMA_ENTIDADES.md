# Sistema de Super Administrador y Entidades

## Descripción

Este sistema implementa una jerarquía de roles con entidades para gestionar múltiples organizaciones dentro del sistema PQRS.

## Jerarquía de Roles

### 1. Super Administrador (`superadmin`)
- **Acceso**: `/soft-admin`
- **Permisos**:
  - Crear, editar y eliminar entidades
  - Crear administradores para cada entidad
  - Ver todos los usuarios del sistema
  - Gestionar el estado de entidades y usuarios

### 2. Administrador (`admin`)
- **Acceso**: `/dashboard`
- **Permisos**:
  - Ver solo usuarios de su entidad
  - Crear secretarios dentro de su entidad
  - Gestionar PQRS de su entidad
  - Ver reportes de su entidad

### 3. Secretario (`secretario`)
- **Acceso**: `/dashboard`
- **Permisos**:
  - Ver PQRS asignadas
  - Procesar PQRS
  - Ver otros secretarios de su entidad

### 4. Ciudadano (`ciudadano`)
- **Acceso**: `/portal-ciudadano`
- **Permisos**:
  - Crear PQRS
  - Ver estado de sus PQRS

## Estructura de Datos

### Entidad (Entity)
```typescript
{
  id: number
  name: string              // Nombre de la entidad
  code: string              // Código único (ej: "SEC-EDUCACION")
  description?: string
  address?: string
  phone?: string
  email?: string
  is_active: boolean
  created_at: datetime
  updated_at?: datetime
}
```

### Usuario (User)
```typescript
{
  id: number
  username: string
  email: string
  full_name: string
  role: 'superadmin' | 'admin' | 'secretario' | 'ciudadano'
  entity_id?: number        // Null para superadmin y ciudadano
  is_active: boolean
  // ... otros campos
}
```

## Instalación y Configuración

### 1. Migración de Base de Datos

Ejecutar el script de migración para crear las tablas necesarias:

```bash
cd backend
python migrate_to_entities.py
```

Este script:
- Crea la tabla `entities`
- Agrega el rol `superadmin` al enum
- Agrega la columna `entity_id` a la tabla `users`
- Crea una entidad por defecto para usuarios existentes

### 2. Crear Super Administrador

Realizar una petición POST al endpoint de inicialización:

```bash
curl -X POST http://localhost:8000/api/auth/init-superadmin
```

Esto creará:
- **Usuario**: `superadmin`
- **Contraseña**: `superadmin123`
- **Email**: `superadmin@sistema.gov.co`

⚠️ **IMPORTANTE**: Cambiar la contraseña inmediatamente después del primer login.

### 3. Primer Login

1. Ir a `/login`
2. Ingresar credenciales:
   - Usuario: `superadmin`
   - Contraseña: `superadmin123`
3. Serás redirigido automáticamente a `/soft-admin`

## Uso del Panel de Super Administrador

### Crear Entidad

1. Acceder a `/soft-admin`
2. Click en "Nueva Entidad"
3. Completar el formulario:
   - **Nombre**: Nombre completo de la entidad
   - **Código**: Código único (ej: "SEC-SALUD")
   - **Descripción**: Descripción opcional
   - **Datos de contacto**: Email, teléfono, dirección

### Crear Administrador de Entidad

1. En el listado de entidades, click en "Crear Admin"
2. Completar el formulario:
   - **Rol**: Admin o Secretario
   - **Nombre de usuario**: Username único
   - **Nombre completo**
   - **Email**
   - **Contraseña**: Mínimo 6 caracteres

### Ver Usuarios de Entidad

1. Click en "Ver Usuarios" en la tarjeta de la entidad
2. Se mostrará la lista de usuarios con sus roles y estados
3. Desde aquí puedes activar/desactivar usuarios

### Activar/Desactivar Entidad

1. Click en "Desactivar" en la tarjeta de la entidad
2. Al desactivar una entidad, todos sus usuarios quedarán inactivos
3. Para reactivar, click en "Activar"

### Eliminar Entidad

⚠️ **ADVERTENCIA**: Esto eliminará todos los usuarios asociados

1. Click en "Eliminar"
2. Confirmar la acción
3. La entidad y todos sus usuarios serán eliminados permanentemente

## API Endpoints

### Entidades

```
GET    /api/entities/              # Listar entidades (superadmin)
POST   /api/entities/              # Crear entidad (superadmin)
GET    /api/entities/{id}          # Obtener entidad (superadmin)
PUT    /api/entities/{id}          # Actualizar entidad (superadmin)
DELETE /api/entities/{id}          # Eliminar entidad (superadmin)
PATCH  /api/entities/{id}/toggle-status  # Activar/desactivar (superadmin)
GET    /api/entities/{id}/users    # Listar usuarios de entidad (superadmin)
```

### Usuarios (actualizados)

```
GET    /api/users/                 # Listar usuarios (filtrado por rol y entidad)
POST   /api/users/                 # Crear usuario
GET    /api/users/{id}             # Obtener usuario
PUT    /api/users/{id}             # Actualizar usuario
DELETE /api/users/{id}             # Eliminar usuario
PATCH  /api/users/{id}/toggle-status  # Activar/desactivar
```

**Filtros disponibles**:
- `?role=admin` - Filtrar por rol
- `?entity_id=1` - Filtrar por entidad (solo superadmin)

### Autenticación

```
POST /api/auth/init-superadmin     # Crear superadmin inicial (solo una vez)
POST /api/auth/init-admin          # Crear admin (legacy, mantener compatibilidad)
POST /api/auth/login               # Login
POST /api/auth/register            # Registro (solo admin/superadmin)
POST /api/auth/register-ciudadano  # Registro público de ciudadanos
GET  /api/auth/me                  # Usuario actual
```

## Flujo de Trabajo Típico

### Configuración Inicial

1. Ejecutar migración de BD
2. Crear superadmin vía API
3. Login como superadmin
4. Crear entidades (ej: Secretaría de Salud, Educación, etc.)
5. Crear admin para cada entidad
6. Los admins crean sus secretarios

### Día a Día

1. **Superadmin**: Gestiona entidades y sus administradores principales
2. **Admin de Entidad**: Gestiona usuarios de su entidad, procesa PQRS
3. **Secretarios**: Procesan PQRS asignadas
4. **Ciudadanos**: Crean y consultan PQRS

## Seguridad

### Middleware de Autorización

El sistema implementa los siguientes decoradores de seguridad:

- `require_superadmin`: Solo superadmin
- `require_admin`: Solo admin
- `require_admin_or_superadmin`: Admin o superadmin
- `check_entity_access`: Verifica acceso a entidad específica

### Guards en Frontend

- `superAdminGuard`: Protege `/soft-admin`
- `authGuard`: Requiere autenticación
- `adminPortalGuard`: Solo admin y secretarios
- `ciudadanoGuard`: Solo ciudadanos

### Validaciones

1. **Separación por entidad**: Admin solo ve/gestiona su entidad
2. **Superadmin aislado**: No pertenece a ninguna entidad
3. **Ciudadanos sin entidad**: Acceso público limitado
4. **Validación de permisos en cada endpoint**

## Cambios en Componentes Existentes

### Login
- Redirige a `/soft-admin` si el usuario es superadmin
- Redirige a `/dashboard` si es admin o secretario
- Redirige a `/portal-ciudadano` si es ciudadano

### Dashboard (a actualizar)
- Admin ve solo PQRS de su entidad
- Secretarios ven solo PQRS asignadas de su entidad

### Gestión de Usuarios (a actualizar)
- Admin solo puede crear usuarios de su entidad
- Filtrado automático por entidad

## Próximos Pasos

1. ✅ Migración de base de datos
2. ✅ Crear superadmin inicial
3. ✅ Acceder al panel de super admin
4. 🔄 Actualizar componente Dashboard para filtrar por entidad
5. 🔄 Actualizar reportes para separar por entidad
6. 🔄 Actualizar gestión de PQRS para filtrar por entidad

## Notas Importantes

- La columna `secretaria` en `users` se mantiene por compatibilidad pero debería migrar a usar `entity_id`
- Los ciudadanos no tienen `entity_id` (null)
- El superadmin no tiene `entity_id` (null)
- Al eliminar una entidad se eliminan todos sus usuarios en cascada
- Al desactivar una entidad se desactivan todos sus usuarios

## Soporte

Para problemas o preguntas sobre el sistema de entidades, revisar:
1. Logs del backend en `/api/docs` (Swagger)
2. Console del navegador en el frontend
3. Errores de migración en la consola del servidor
