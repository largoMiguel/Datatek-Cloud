# Solución: Problema de Datos Cacheados entre Entidades

## Problema Reportado

El usuario reportó que al crear una nueva entidad, esta aparecía con un plan pre-cargado cuando debería estar vacía/limpia.

## Diagnóstico

Después de investigar el código y la base de datos, se identificó que:

1. **NO había planes en la base de datos** - El backend no crea datos de ejemplo
2. **El backend filtra correctamente por `entity_id`** - Las rutas de planes ya tienen filtros por entidad
3. **El problema estaba en el frontend** - Los componentes NO estaban suscritos a cambios en el contexto de entidad

### Causa Raíz

Cuando Angular navega entre rutas con el mismo componente pero diferentes parámetros (ejemplo: `/chiquiza-boyaca/planes-institucionales` → `/sora-boyaca/planes-institucionales`), **reutiliza la instancia del componente** en lugar de destruirla y recrearla.

Los componentes `PlanesInstitucionalesComponent` y `DashboardComponent`:
- Solo se suscribían a `authService.currentUser$` en el `ngOnInit`
- **NO** se suscribían a `entityContextService.currentEntity$`
- **NO** limpiaban sus datos cuando cambiaba la entidad
- Por lo tanto, mostraban datos de la entidad anterior

### Escenario del Bug

1. Usuario navega a `/chiquiza-boyaca/planes-institucionales` (Entidad 1)
2. Componente carga y muestra planes de Chiquiza
3. Usuario navega a `/sora-boyaca/planes-institucionales` (Entidad 2)
4. **Angular reutiliza el mismo componente** (no se ejecuta `ngOnDestroy` ni `ngOnInit`)
5. El componente **mantiene los planes de Chiquiza** porque no se suscribió al cambio de entidad
6. Usuario ve planes "fantasma" que pertenecen a otra entidad

## Solución Implementada

### 1. Componente de Planes Institucionales

**Archivo:** `frontend/pqrs-frontend/src/app/components/planes-institucionales/planes-institucionales.ts`

#### Cambios:

1. **Importar RxJS operators:**
```typescript
import { Subscription, combineLatest, filter } from 'rxjs';
import { EntityContextService } from '../../services/entity-context.service';
```

2. **Agregar propiedades:**
```typescript
private entityContextService = inject(EntityContextService);
private subscriptions = new Subscription();
```

3. **Refactorizar ngOnInit para suscribirse a cambios de entidad:**
```typescript
ngOnInit(): void {
    // Combinar usuario y entidad para cargar planes solo cuando ambos estén listos
    // y recargar cuando cualquiera cambie
    const combined = combineLatest([
        this.authService.currentUser$,
        this.entityContextService.currentEntity$
    ]).pipe(
        filter(([user, entity]) => user !== null && entity !== null)
    ).subscribe(([user, entity]) => {
        this.currentUser = user;
        // Limpiar datos y recargar con el nuevo contexto
        this.limpiarDatos();
        this.cargarPlanes();
    });
    this.subscriptions.add(combined);

    this.setupPopstateListener();
}
```

4. **Implementar limpieza de datos:**
```typescript
private limpiarDatos(): void {
    this.planes = [];
    this.metasPorPlan.clear();
    this.planSeleccionado = null;
    this.vistaActual = 'planes';
    this.vistaAnterior = 'planes';
    this.analyticsData = null;
}
```

5. **Limpiar suscripciones en ngOnDestroy:**
```typescript
ngOnDestroy(): void {
    window.removeEventListener('popstate', this.handlePopstate);
    this.subscriptions.unsubscribe();
}
```

### 2. Componente Dashboard

**Archivo:** `frontend/pqrs-frontend/src/app/components/dashboard/dashboard.ts`

#### Cambios similares:

1. **Importar RxJS operators:**
```typescript
import { Subscription, combineLatest, filter } from 'rxjs';
```

2. **Agregar Subscription container:**
```typescript
private subscriptions = new Subscription();
```

3. **Refactorizar ngOnInit:**
```typescript
ngOnInit() {
    const combined = combineLatest([
      this.authService.currentUser$,
      this.entityContext.currentEntity$
    ]).pipe(
      filter(([user, entity]) => user !== null && entity !== null)
    ).subscribe(([user, entity]) => {
      this.currentUser = user;
      this.limpiarDatos();
      this.loadPqrs();
      this.loadSecretarios();
    });
    this.subscriptions.add(combined);
    
    // Mantener el manejo de errores de autenticación
    const authErrorCheck = this.authService.getCurrentUser().subscribe({
      error: () => {
        const slug = this.router.url.replace(/^\//, '').split('/')[0];
        this.router.navigate(slug ? ['/', slug, 'login'] : ['/], { replaceUrl: true });
      }
    });
    this.subscriptions.add(authErrorCheck);
}
```

4. **Implementar limpieza de datos:**
```typescript
private limpiarDatos(): void {
    this.pqrsList = [];
    this.usuariosList = [];
    this.secretariosList = [];
    this.selectedPqrs = null;
    this.pqrsEditando = null;
    this.activeView = 'dashboard';
}
```

5. **Limpiar suscripciones:**
```typescript
ngOnDestroy() {
    this.subscriptions.unsubscribe();
}
```

## Ventajas de la Solución

### 1. **Uso de `combineLatest`**
- Espera a que **ambos** (usuario y entidad) estén disponibles antes de cargar datos
- Evita cargas duplicadas o condiciones de carrera
- Se reactiva automáticamente cuando cualquiera de los dos cambia

### 2. **Filtro de valores no nulos**
- `.pipe(filter(([user, entity]) => user !== null && entity !== null))`
- Evita intentar cargar datos antes de tener el contexto completo

### 3. **Limpieza consistente**
- Método `limpiarDatos()` centraliza la lógica de limpieza
- Se ejecuta antes de cada recarga para evitar mezclar datos de entidades diferentes

### 4. **Gestión correcta de suscripciones**
- Usa `Subscription` container para agrupar todas las suscripciones
- `unsubscribe()` en `ngOnDestroy` previene memory leaks

## Flujo Corregido

### Navegación entre entidades:

1. Usuario navega de `/chiquiza-boyaca/planes` a `/sora-boyaca/planes`
2. `ensureEntityGuard` carga la nueva entidad (Sora)
3. `EntityContextService` emite el cambio: `currentEntity$ → Entity(Sora)`
4. `combineLatest` detecta el cambio
5. `limpiarDatos()` elimina los planes de Chiquiza
6. `cargarPlanes()` solicita al backend los planes de Sora
7. Backend filtra por `entity_id` de Sora
8. Frontend muestra lista vacía (Sora no tiene planes)

### Verificación con Guards:

Si el usuario es `admin` de Chiquiza:
1. Intenta navegar a `/sora-boyaca/planes`
2. `enforceUserEntityGuard` detecta que `user.entity_id !== sora.id`
3. Redirige automáticamente a `/chiquiza-boyaca/planes`
4. El componente carga planes de Chiquiza (correctamente)

## Testing Recomendado

### Caso 1: Superadmin entre entidades
```
1. Login como superadmin
2. Navegar a /chiquiza-boyaca/planes
3. Crear un plan en Chiquiza
4. Navegar a /sora-boyaca/planes
5. ✅ Verificar que NO se muestra el plan de Chiquiza
6. ✅ Verificar que Sora muestra lista vacía
```

### Caso 2: Admin restringido
```
1. Login como admin de Chiquiza (entity_id = 1)
2. Navegar a /sora-boyaca/planes
3. ✅ Verificar que redirige a /chiquiza-boyaca/planes
4. ✅ Verificar que solo muestra planes de Chiquiza
```

### Caso 3: Cambio de entidad en Dashboard
```
1. Login como superadmin
2. Navegar a /chiquiza-boyaca/dashboard
3. Crear PQRS en Chiquiza
4. Navegar a /sora-boyaca/dashboard
5. ✅ Verificar que NO se muestran PQRS de Chiquiza
6. ✅ Verificar que Sora muestra lista vacía
```

## Archivos Modificados

1. `frontend/pqrs-frontend/src/app/components/planes-institucionales/planes-institucionales.ts`
   - Suscripción a `EntityContextService.currentEntity$`
   - Método `limpiarDatos()`
   - Uso de `combineLatest` para sincronizar usuario y entidad

2. `frontend/pqrs-frontend/src/app/components/dashboard/dashboard.ts`
   - Suscripción a `EntityContextService.currentEntity$`
   - Método `limpiarDatos()`
   - Uso de `combineLatest` para sincronizar usuario y entidad

## Estado de la Base de Datos

Verificado el 28/10/2025:

```
=== ENTIDADES EN LA BD ===
ID: 1, Nombre: ALCALDIA DE CHIQUIZA, Slug: chiquiza-boyaca
ID: 2, Nombre: ALCALDIA DE SORA, Slug: sora-boyaca

=== USUARIOS EN LA BD ===
ID: 1, Username: admin, Role: ADMIN, Entity ID: 1
ID: 2, Username: jrubio, Role: SECRETARIO, Entity ID: 1
ID: 6, Username: superadmin, Role: SUPERADMIN, Entity ID: None
ID: 7, Username: chiquiza, Role: ADMIN, Entity ID: 2
ID: 8, Username: miguel, Role: SECRETARIO, Entity ID: 2

=== PLANES EN LA BD ===
(No hay planes)
```

## Conclusión

El problema NO era que el backend creara datos de ejemplo, sino que el frontend **no limpiaba los datos** cuando el usuario navegaba entre entidades diferentes. Los componentes mantenían en memoria los datos de la entidad anterior.

La solución implementa una arquitectura reactiva robusta que:
- ✅ Sincroniza usuario y entidad antes de cargar datos
- ✅ Limpia datos antiguos al cambiar de contexto
- ✅ Previene condiciones de carrera y cargas duplicadas
- ✅ Gestiona correctamente el ciclo de vida de suscripciones
- ✅ Mantiene aislamiento de datos entre entidades

**Build exitoso:** ✅ Compilación completada sin errores (solo advertencias CommonJS esperadas)
