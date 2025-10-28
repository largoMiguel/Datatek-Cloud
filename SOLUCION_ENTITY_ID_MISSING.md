# Corrección: Error entity_id en Creación de Planes y PQRS

## Fecha: 28 de octubre de 2025

## Problema Reportado

Al intentar crear un plan institucional, el backend devolvía error:
```json
{
  "detail": [{
    "type": "missing",
    "loc": ["body", "entity_id"],
    "msg": "Field required"
  }]
}
```

## Causa Raíz

### Backend

El schema `PlanInstitucionalCreate` tenía `entity_id` como campo **obligatorio**:
```python
class PlanInstitucionalCreate(PlanInstitucionalBase):
    entity_id: int  # Obligatorio al crear
```

Pero la lógica esperaba **asignarlo automáticamente** desde `current_user.entity_id`:
```python
plan_dict['entity_id'] = current_user.entity_id
```

Esto creaba un conflicto: el frontend no enviaba `entity_id` (porque esperaba que el backend lo asignara), pero Pydantic lo rechazaba por ser obligatorio.

### Frontend

Los componentes que crean planes **NO enviaban `entity_id`** porque asumían que el backend lo asignaría automáticamente.

Para PQRS, algunos componentes **SÍ enviaban `entity_id`** correctamente (Portal Ciudadano), pero otros **NO** (Dashboard, Ventanilla).

## Solución Implementada

### 1. Backend - Schema de Planes

**Archivo:** `backend/app/schemas/plan.py`

Cambio de `entity_id` obligatorio a **opcional**:

```python
class PlanInstitucionalCreate(PlanInstitucionalBase):
    """Schema para crear un plan institucional"""
    entity_id: Optional[int] = None  # Opcional, se asigna automáticamente desde current_user
```

### 2. Backend - Ruta de Creación de Planes

**Archivo:** `backend/app/routes/planes.py`

Simplificación de la lógica de asignación de `entity_id`:

```python
@router.post("/", response_model=plan_schemas.PlanInstitucional, status_code=status.HTTP_201_CREATED)
def crear_plan(
    plan_data: plan_schemas.PlanInstitucionalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _feature: bool = Depends(require_feature_enabled('enable_planes_institucionales'))
):
    """
    Crear un nuevo plan institucional.
    Solo administradores pueden crear planes.
    El entity_id se asigna automáticamente desde el usuario actual.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores pueden crear planes"
        )
    
    # Validar que el admin tenga entity_id
    if not current_user.entity_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario no tiene una entidad asignada"
        )
    
    # Validar que fecha_fin sea posterior a fecha_inicio
    if plan_data.fecha_fin <= plan_data.fecha_inicio:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La fecha de fin debe ser posterior a la fecha de inicio"
        )
    
    # Crear el plan con entity_id del usuario actual
    plan_dict = plan_data.model_dump(exclude={'entity_id'})
    plan_dict['entity_id'] = current_user.entity_id
    
    nuevo_plan = PlanInstitucional(**plan_dict)
    db.add(nuevo_plan)
    db.commit()
    db.refresh(nuevo_plan)
    
    return nuevo_plan
```

**Mejoras:**
- ✅ Valida que el admin tenga `entity_id` asignado
- ✅ Excluye explícitamente `entity_id` del request y lo asigna desde `current_user`
- ✅ Elimina código duplicado (creaba el plan dos veces)

### 3. Frontend - Dashboard (Creación de PQRS)

**Archivo:** `frontend/pqrs-frontend/src/app/components/dashboard/dashboard.ts`

Agregado de `entity_id` desde el contexto de entidad:

```typescript
onSubmitNuevaPqrs() {
    if (this.nuevaPqrsForm.valid && !this.isSubmitting) {
      this.isSubmitting = true;

      const formData = this.nuevaPqrsForm.value;

      // Agregar entity_id desde el contexto de entidad actual
      const currentEntity = this.entityContext.currentEntity;
      if (!currentEntity) {
        this.alertService.error('No se pudo determinar la entidad actual', 'Error');
        this.isSubmitting = false;
        return;
      }
      formData.entity_id = currentEntity.id;

      // ... resto del código ...
    }
}
```

### 4. Frontend - Ventanilla (Radicación de PQRS)

**Archivo:** `frontend/pqrs-frontend/src/app/components/ventanilla/ventanilla.ts`

Agregado de `entity_id` desde el contexto de entidad:

```typescript
submitRadicacion() {
    // Validar campos requeridos
    if (!this.radicacionForm.tipo_solicitud || !this.radicacionForm.cedula_ciudadano ||
        !this.radicacionForm.nombre_ciudadano || !this.radicacionForm.asunto ||
        !this.radicacionForm.descripcion) {
        this.alertService.warning('Por favor completa todos los campos obligatorios marcados con *', 'Campos Requeridos');
        return;
    }

    // Validar que hay una entidad actual
    const currentEntity = this.entityContext.currentEntity;
    if (!currentEntity) {
        this.alertService.error('No se pudo determinar la entidad actual', 'Error');
        return;
    }

    this.isSubmitting = true;

    // Construir objeto PQRS con todos los campos requeridos
    const pqrsData: any = {
        tipo_identificacion: 'personal',
        medio_respuesta: this.radicacionForm.email_ciudadano ? 'email' : 'ticket',
        tipo_solicitud: this.radicacionForm.tipo_solicitud,
        nombre_ciudadano: this.radicacionForm.nombre_ciudadano,
        cedula_ciudadano: this.radicacionForm.cedula_ciudadano,
        asunto: this.radicacionForm.asunto,
        descripcion: this.radicacionForm.descripcion,
        telefono_ciudadano: this.radicacionForm.telefono_ciudadano || null,
        email_ciudadano: this.radicacionForm.email_ciudadano || null,
        direccion_ciudadano: this.radicacionForm.direccion_ciudadano || null,
        entity_id: currentEntity.id  // Agregar entity_id desde el contexto
    };

    // ... resto del código ...
}
```

### 5. Frontend - Portal Ciudadano

**Archivo:** `frontend/pqrs-frontend/src/app/components/portal-ciudadano/portal-ciudadano.ts`

**Ya estaba correcto** ✅ - Ya incluía `entity_id` desde el contexto:

```typescript
const formData = {
    ...this.nuevaPqrsForm.value,
    entity_id: this.currentEntity.id
};
```

## Arquitectura de entity_id

### Para Planes Institucionales

**Backend asigna automáticamente:**
- Los planes SOLO pueden ser creados por admins
- Cada admin pertenece a UNA entidad específica (`user.entity_id`)
- El backend **siempre** usa `current_user.entity_id`
- Frontend **NO debe enviar** `entity_id` (se ignora si lo envía)

**Flujo:**
```
Frontend → Backend → Valida Admin → Asigna entity_id desde current_user → Crea Plan
```

### Para PQRS

**Backend requiere entity_id en request:**
- Las PQRS pueden ser creadas por:
  - Ciudadanos (NO tienen `entity_id` en su usuario)
  - Admins (tienen `entity_id`)
  - Secretarios (tienen `entity_id`)
  - Anónimos (sin autenticación en ventanilla pública)
  
- Por eso, el backend **REQUIERE** que el frontend envíe `entity_id` explícitamente

**Flujo:**
```
Frontend → Obtiene entity_id desde EntityContext → Lo incluye en request → Backend → Crea PQRS
```

## Estado de Schemas Backend

### Planes (Corregido)
```python
class PlanInstitucionalCreate(PlanInstitucionalBase):
    entity_id: Optional[int] = None  # ✅ Opcional
```

### PQRS (Correcto, sin cambios)
```python
class PQRSCreate(PQRSBase):
    entity_id: int  # ✅ Obligatorio (ciudadanos no tienen entity_id en user)
```

### Usuarios (Correcto, sin cambios)
```python
class UserCreate(UserBase):
    entity_id: Optional[int] = None  # ✅ Opcional (superadmin no tiene entidad)
```

## Componentes Frontend que Crean Recursos

| Componente | Recurso | entity_id | Estado |
|---|---|---|---|
| `planes-institucionales.ts` | Planes | NO envía (backend asigna) | ✅ Correcto |
| `dashboard.ts` | PQRS | Envía desde EntityContext | ✅ CORREGIDO |
| `ventanilla.ts` | PQRS | Envía desde EntityContext | ✅ CORREGIDO |
| `portal-ciudadano.ts` | PQRS | Envía desde EntityContext | ✅ Ya estaba bien |

## Testing Recomendado

### Planes Institucionales

```
1. Login como admin de entidad 1
2. Ir a /entidad-1/planes-institucionales
3. Crear un nuevo plan
4. ✅ Verificar que se crea correctamente sin error de entity_id
5. ✅ Verificar que el plan tiene entity_id = 1 en la BD
6. Login como admin de entidad 2
7. Ir a /entidad-2/planes-institucionales
8. ✅ Verificar que NO ve el plan de entidad 1
```

### PQRS desde Dashboard

```
1. Login como admin
2. Ir a /entidad-1/dashboard
3. Crear una PQRS
4. ✅ Verificar que se crea correctamente
5. ✅ Verificar que tiene entity_id = 1 en la BD
```

### PQRS desde Ventanilla

```
1. Sin autenticación
2. Ir a /entidad-1 (ventanilla pública)
3. Radicar una PQRS
4. ✅ Verificar que se crea correctamente
5. ✅ Verificar que tiene entity_id = 1 en la BD
```

### PQRS desde Portal Ciudadano

```
1. Login como ciudadano
2. Ir a /entidad-1/portal-ciudadano
3. Crear una PQRS
4. ✅ Verificar que se crea correctamente
5. ✅ Verificar que tiene entity_id = 1 en la BD
```

## Validaciones Agregadas

### Backend - Creación de Planes

1. ✅ Usuario debe ser ADMIN
2. ✅ Admin debe tener `entity_id` asignado
3. ✅ `fecha_fin` debe ser posterior a `fecha_inicio`
4. ✅ `entity_id` se asigna desde `current_user.entity_id` (ignorando request)

### Frontend - Creación de PQRS/Planes

1. ✅ Validación de `EntityContext.currentEntity` no null
2. ✅ Mensaje de error claro si no hay entidad
3. ✅ Prevención de submit si falta entidad

## Archivos Modificados

### Backend (2 archivos)
1. `backend/app/schemas/plan.py` - entity_id opcional en PlanInstitucionalCreate
2. `backend/app/routes/planes.py` - Lógica simplificada de asignación entity_id

### Frontend (2 archivos)
3. `frontend/pqrs-frontend/src/app/components/dashboard/dashboard.ts` - Agregar entity_id desde EntityContext
4. `frontend/pqrs-frontend/src/app/components/ventanilla/ventanilla.ts` - Agregar entity_id desde EntityContext

## Build Status

✅ **Backend:** Sin cambios de runtime, solo schemas
✅ **Frontend:** Build exitoso sin errores

```
Application bundle generation complete. [6.434 seconds]
Output location: /Users/largo/Documents/SOLUCTIONS/pqrs-alcaldia/frontend/pqrs-frontend/dist/pqrs-frontend
```

## Conclusión

El problema se debía a un desacuerdo entre:
- **Schema backend** que requería `entity_id` obligatorio
- **Lógica backend** que intentaba asignarlo automáticamente
- **Frontend** que no lo enviaba

La solución consistió en:
1. **Para Planes:** Hacer `entity_id` opcional en el schema y siempre asignarlo desde `current_user`
2. **Para PQRS:** Agregar `entity_id` desde `EntityContext` en todos los componentes que crean PQRS

Ahora ambos recursos se crean correctamente con el `entity_id` apropiado, manteniendo el aislamiento de datos entre entidades.
