# Fix: Corrección de Permisos Modulares por Usuario

## Problema Reportado
Usuario creó un contratista y al ingresar al sistema:
- Aparecía como secretario (problema visual corregido)
- No respetaba los módulos activados por el admin
- Veía todas las pestañas/módulos sin importar los permisos asignados

## Causa Raíz
El dashboard verificaba solo si los módulos estaban activos en la entidad (`pqrsEnabled()`, `planesEnabled()`, `contratacionEnabled()`), pero **NO verificaba los permisos del usuario** (`allowed_modules`).

## Solución Implementada

### 1. Backend (Ya existente y funcionando)
✅ Base de datos con `user_type` y `allowed_modules`
✅ Validación en POST/PUT `/api/users/` contra módulos activos de la entidad
✅ Formulario envía correctamente `user_type` y `allowed_modules`

### 2. Frontend - Dashboard TypeScript (`dashboard.ts`)

#### Métodos Agregados:
```typescript
// Verifica si el usuario tiene un módulo específico
userHasModule(moduleName: string): boolean {
  const user = this.currentUser;
  if (!user) return false;
  
  // Admin siempre tiene acceso
  if (user.role === 'admin' || user.role === 'superadmin') {
    return true;
  }
  
  // Si no tiene allowed_modules (usuario legacy), tiene acceso a todo
  if (!user.allowed_modules || user.allowed_modules.length === 0) {
    return true;
  }
  
  return user.allowed_modules.includes(moduleName);
}

// Combina verificación de entidad + permisos de usuario
canAccessPqrs(): boolean {
  return this.pqrsEnabled() && this.userHasModule('pqrs');
}

canAccessPlanes(): boolean {
  return this.planesEnabled() && this.userHasModule('planes_institucionales');
}

canAccessContratacion(): boolean {
  return this.contratacionEnabled() && this.userHasModule('contratacion');
}
```

### 3. Frontend - Dashboard HTML (`dashboard.html`)

#### Pestañas Actualizadas (líneas 70-106):
```html
<!-- Antes -->
<a class="nav-link" *ngIf="pqrsEnabled()" ...>Mis PQRS</a>
<a class="nav-link" *ngIf="planesEnabled()" ...>Planes</a>
<a class="nav-link" *ngIf="contratacionEnabled()" ...>Contratación</a>

<!-- Después -->
<a class="nav-link" *ngIf="canAccessPqrs()" ...>Mis PQRS</a>
<a class="nav-link" *ngIf="canAccessPlanes()" ...>Planes</a>
<a class="nav-link" *ngIf="canAccessContratacion()" ...>Contratación</a>
```

#### Vistas de Contenido Actualizadas:
```html
<!-- Dashboard View -->
<div *ngIf="activeView === 'dashboard' && canAccessPqrs()">

<!-- Mensaje cuando no tiene acceso -->
<div *ngIf="activeView === 'dashboard' && !canAccessPqrs()" class="card">
  <p>El módulo de PQRS está desactivado para esta entidad o no tienes permisos para acceder.</p>
</div>

<!-- Mis PQRS View -->
<div *ngIf="activeView === 'mis-pqrs' && canAccessPqrs()">

<!-- Nueva PQRS View -->
<div *ngIf="activeView === 'nueva-pqrs' && canAccessPqrs()">
```

### 4. Route Guards (`module-access.guard.ts`)

Nuevo guard para prevenir navegación directa por URL:

```typescript
export const moduleAccessGuard = (requiredModule: string): CanActivateFn => {
  return () => {
    const authService = inject(AuthService);
    const router = inject(Router);
    
    const currentUser = authService.getCurrentUserValue();
    
    if (!currentUser) {
      router.navigate(['/login']);
      return false;
    }
    
    // Admin siempre tiene acceso
    if (currentUser.role === 'admin' || currentUser.role === 'superadmin') {
      return true;
    }
    
    // Usuario legacy (sin allowed_modules) tiene acceso completo
    if (!currentUser.allowed_modules) {
      return true;
    }
    
    // Verifica que el módulo esté en la lista permitida
    const hasAccess = currentUser.allowed_modules.includes(requiredModule);
    
    if (!hasAccess) {
      router.navigate(['/dashboard']);
      return false;
    }
    
    return true;
  };
};
```

### 5. Rutas Protegidas (`app.routes.ts`)

```typescript
{ 
  path: 'portal-ciudadano', 
  component: PortalCiudadanoComponent, 
  canActivate: [ciudadanoGuard, pqrsEnabledGuard, moduleAccessGuard('pqrs')] 
},
{ 
  path: 'planes-institucionales', 
  component: PlanesInstitucionalesComponent, 
  canActivate: [adminPortalGuard, enforceUserEntityGuard, planesEnabledGuard, moduleAccessGuard('planes_institucionales')] 
},
{ 
  path: 'contratacion', 
  component: ContratacionComponent, 
  canActivate: [adminPortalGuard, enforceUserEntityGuard, contratacionEnabledGuard, moduleAccessGuard('contratacion')] 
}
```

## Flujo de Verificación

### Doble Capa de Seguridad:

1. **Entidad**: ¿El módulo está activo en la entidad?
   - `entity.enable_pqrs`
   - `entity.enable_planes_institucionales`
   - `entity.enable_contratacion`

2. **Usuario**: ¿El usuario tiene permiso para ese módulo?
   - `user.allowed_modules = ['pqrs', 'planes_institucionales']`

### Lógica de Acceso:
```typescript
canAccessModule = entityHasModuleEnabled() && userHasModulePermission()
```

## Comportamiento por Rol

### ADMIN / SUPERADMIN:
- ✅ Bypass completo de verificación de `allowed_modules`
- ✅ Solo respeta si la entidad tiene el módulo activo
- ✅ Puede gestionar todos los módulos activos de su entidad

### SECRETARIO / CONTRATISTA:
- ✅ Debe tener el módulo en `allowed_modules`
- ✅ La entidad debe tener el módulo activo
- ❌ Si falta cualquiera de las dos condiciones, no tiene acceso

### Usuario Legacy (sin `allowed_modules`):
- ✅ Comportamiento anterior preservado
- ✅ Acceso a todos los módulos activos de la entidad
- 📌 Compatibilidad hacia atrás garantizada

## Testing

### Caso 1: Contratista con solo Planes
```json
{
  "username": "contratista1",
  "user_type": "contratista",
  "allowed_modules": ["planes_institucionales"]
}
```

**Resultado Esperado:**
- ✅ Ve pestaña "Dashboard"
- ✅ Ve pestaña "Planes Institucionales"
- ❌ NO ve pestaña "Mis PQRS"
- ❌ NO ve pestaña "Nueva PQRS"
- ❌ NO ve pestaña "Contratación"
- ❌ URL directa a `/contratacion` redirige a `/dashboard`

### Caso 2: Secretario con PQRS y Contratación
```json
{
  "username": "secretario1",
  "user_type": "secretario",
  "allowed_modules": ["pqrs", "contratacion"]
}
```

**Resultado Esperado:**
- ✅ Ve pestañas de PQRS
- ✅ Ve pestaña de Contratación
- ❌ NO ve pestaña de Planes

### Caso 3: Admin
```json
{
  "username": "admin1",
  "role": "admin"
}
```

**Resultado Esperado:**
- ✅ Ve todos los módulos activos en la entidad
- ✅ No se aplica filtro de `allowed_modules`

## Archivos Modificados

### Frontend:
- `src/app/components/dashboard/dashboard.ts` - Métodos de verificación
- `src/app/components/dashboard/dashboard.html` - Condicionales de UI
- `src/app/guards/module-access.guard.ts` - **NUEVO** Guard de rutas
- `src/app/app.routes.ts` - Guards aplicados a rutas

### Backend (sin cambios en este fix):
- Ya funciona correctamente

## Deployment

### No requiere migración de base de datos
Los cambios son solo de frontend (lógica de visualización y routing).

### Pasos:
1. Commit de cambios frontend
2. Deploy frontend
3. Probar con usuarios existentes y nuevos

## Notas Importantes

⚠️ **Checkboxes del Formulario**: Los checkboxes en el formulario de "Nuevo Usuario" usan `pqrsEnabled()`, `planesEnabled()`, `contratacionEnabled()` (sin cambios). Esto es correcto porque el admin necesita ver qué módulos están disponibles en la entidad para asignarlos.

✅ **Compatibilidad**: Usuarios creados antes de la feature de `allowed_modules` (con valor NULL) mantienen acceso completo.

🔒 **Seguridad Completa**: 
- Pestañas ocultas en UI
- Vistas de contenido protegidas
- Rutas protegidas con guards
- Previene manipulación de URL

## Documentos Relacionados
- `PERMISOS_MODULARES_USUARIOS.md` - Documentación inicial de la feature
- `backend/add_user_modules_columns.py` - Script de migración (ya ejecutado)
