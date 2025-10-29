# Sistema de Permisos Modulares por Usuario

## Resumen de Cambios

Se ha implementado un sistema de permisos granulares que permite asignar módulos específicos a cada usuario (secretarios y contratistas). Esto permite que cada entidad pueda:

- Crear usuarios de tipo **Secretario** o **Contratista**
- Asignar módulos específicos a cada usuario: PQRS, Planes Institucionales, Contratación
- Controlar el acceso basado en los módulos activos de la entidad

## Cambios en Backend

### 1. Modelo de Usuario (`app/models/user.py`)

**Nuevos campos:**
- `user_type`: Enum con valores `secretario` | `contratista` (opcional, solo para usuarios no admin)
- `allowed_modules`: Array JSON con los módulos permitidos: `["pqrs", "planes_institucionales", "contratacion"]`

**Nuevo Enum:**
```python
class UserType(enum.Enum):
    SECRETARIO = "secretario"
    CONTRATISTA = "contratista"
```

### 2. Schemas (`app/schemas/user.py`)

Actualizados `UserBase`, `UserCreate` y `UserUpdate` para incluir:
- `user_type: Optional[UserType]`
- `allowed_modules: Optional[List[str]]`

### 3. Rutas de Usuarios (`app/routes/users.py`)

**Validaciones agregadas:**
- Al crear/actualizar usuario, valida que los módulos asignados estén activos en la entidad
- Verifica contra los flags: `enable_pqrs`, `enable_planes_institucionales`, `enable_contratacion`
- Retorna error 400 si se intenta asignar un módulo inactivo

**Ejemplo de validación:**
```python
if entity.enable_pqrs:
    valid_modules.append("pqrs")
if entity.enable_planes_institucionales:
    valid_modules.append("planes_institucionales")
if entity.enable_contratacion:
    valid_modules.append("contratacion")
```

## Cambios en Frontend

### 1. Modelo de Usuario (`models/user.model.ts`)

```typescript
export interface User {
    // ... campos existentes
    user_type?: 'secretario' | 'contratista' | null;
    allowed_modules?: string[];  // ["pqrs", "planes_institucionales", "contratacion"]
}
```

### 2. Formulario de Creación de Usuarios

**Dashboard (`components/dashboard/`):**

**Nuevos campos en el formulario:**
- Selector de **Tipo de Usuario**: Secretario | Contratista
- Checkboxes de **Módulos Permitidos**:
  - ✓ PQRS
  - ✓ Planes Institucionales
  - ✓ Contratación

**Características:**
- Solo muestra módulos activos en la entidad actual
- Requiere seleccionar al menos un módulo
- Valida antes de permitir submit

**Botón actualizado:**
- Antes: "Nuevo Secretario"
- Ahora: "Nuevo Usuario"

### 3. Tabla de Usuarios

**Nuevas columnas:**
- **Tipo**: Secretario | Contratista
- **Módulos**: Badges con iconos (PQRS 📥, Planes ✓, Contratación 📄)

### 4. Lógica del Componente

**Nuevos métodos:**
```typescript
hasAnyModuleSelected(): boolean
getModuleName(module: string): string
```

**Formulario actualizado:**
```typescript
nuevoSecretarioForm = this.fb.group({
  // ... campos existentes
  user_type: ['', Validators.required],
  module_pqrs: [false],
  module_planes: [false],
  module_contratacion: [false],
})
```

## Migración de Base de Datos

### Script de Migración

**Archivo:** `backend/add_user_modules_columns.py`

**Ejecutar en producción:**
```bash
cd backend
python add_user_modules_columns.py
```

**Qué hace:**
1. Crea el ENUM `usertype` (PostgreSQL) con valores: `secretario`, `contratista`
2. Añade columna `user_type` (NULL, tipo ENUM o VARCHAR según DB)
3. Añade columna `allowed_modules` (NULL, tipo JSON o TEXT según DB)

**Seguro:**
- Verifica si las columnas ya existen antes de crearlas
- No modifica datos existentes
- Compatible con PostgreSQL y SQLite

### Usuarios Existentes

Los usuarios creados antes de esta actualización:
- Tendrán `user_type = NULL` (es válido)
- Tendrán `allowed_modules = NULL` o `[]` (acceso a todos los módulos por defecto)

## Cambios en Showcase

### Módulo de Gestión de Usuarios

**Antes:**
- Mencionaba "Super admin con control multi-entidad"

**Ahora:**
- Enfoque en roles entregables al cliente: Admin, Secretarios, Contratistas
- Descripción: "Control total de usuarios, permisos y accesos. Sistema de roles jerárquicos con administradores, secretarios, contratistas y portal ciudadano."

**Features actualizadas:**
- ✅ Admin por entidad con gestión local
- ✅ Secretarios y contratistas con permisos por módulo
- ✅ Asignación granular de módulos permitidos
- ✅ Portal ciudadano sin registro necesario
- ✅ Control de acceso por módulos activos
- ✅ Gestión simplificada de equipos de trabajo

## Pasos de Despliegue

### 1. Backend

```bash
# En Render o servidor de producción
cd /ruta/a/backend

# Ejecutar migración
python add_user_modules_columns.py

# Verificar que no haya errores
# Reiniciar servidor si es necesario
```

### 2. Frontend

```bash
# Build de producción
cd frontend/pqrs-frontend
npm run build:prod

# Deploy automático en Render/Netlify tras push a master
```

### 3. Verificación

1. **Backend:**
   - GET `/api/users/` debe retornar usuarios con campos `user_type` y `allowed_modules`

2. **Frontend:**
   - Navegar a Dashboard → Usuarios
   - Click en "Nuevo Usuario"
   - Verificar que aparecen:
     - Selector de Tipo de Usuario
     - Checkboxes de Módulos (según módulos activos)
   - Crear un usuario de prueba
   - Verificar que aparece en la tabla con tipo y módulos

3. **Showcase:**
   - Navegar a `/showcase`
   - Verificar que NO se menciona "super admin" en Gestión de Usuarios
   - Verificar que se mencionan secretarios y contratistas

## Uso del Sistema

### Como Admin de Entidad

1. **Crear usuario:**
   - Dashboard → Usuarios → Nuevo Usuario
   - Completar datos básicos
   - Seleccionar tipo: Secretario o Contratista
   - Marcar módulos permitidos (solo aparecen los activos)
   - Guardar

2. **Resultado:**
   - El usuario solo podrá acceder a los módulos asignados
   - Si se desactiva un módulo en la entidad, los usuarios ya no podrán acceder aunque lo tengan asignado

### Validaciones

- ❌ No se puede asignar un módulo inactivo en la entidad
- ❌ No se puede crear usuario sin seleccionar al menos un módulo
- ❌ No se puede crear usuario sin seleccionar tipo (secretario/contratista)

## Próximos Pasos (Opcional)

### Guards de Frontend

Para implementar guards que verifiquen `allowed_modules`:

```typescript
// app/guards/module-access.guard.ts
export const moduleAccessGuard = (requiredModule: string) => {
  return () => {
    const authService = inject(AuthService);
    const router = inject(Router);
    const user = authService.getCurrentUserValue();
    
    // Admin siempre tiene acceso
    if (user?.role === 'admin') return true;
    
    // Verificar si tiene el módulo asignado
    if (!user?.allowed_modules?.includes(requiredModule)) {
      router.navigate(['/unauthorized']);
      return false;
    }
    
    return true;
  };
};
```

**Uso en rutas:**
```typescript
{
  path: 'planes-institucionales',
  component: PlanesInstitucionalesComponent,
  canActivate: [
    adminPortalGuard,
    planesEnabledGuard,
    moduleAccessGuard('planes_institucionales')  // NUEVO
  ]
}
```

## Soporte

Para preguntas o problemas:
- Revisar logs del backend: `/var/log/` o Render Logs
- Verificar consola del navegador (F12)
- Ejecutar diagnóstico: `backend/diagnose_prod.sh`
