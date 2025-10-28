import { inject } from '@angular/core';
import { Router, CanActivateFn } from '@angular/router';
import { map, catchError, of } from 'rxjs';
import { EntityService } from '../services/entity.service';

export const defaultEntityGuard: CanActivateFn = (route, state) => {
    const entityService = inject(EntityService);
    const router = inject(Router);

    // Intentar obtener la primera entidad activa como por defecto
    return entityService.getPublicEntities().pipe(
        map(entities => {
            if (entities && entities.length > 0) {
                const defaultEntity = entities.find(e => e.is_active) || entities[0];
                router.navigate(['/', defaultEntity.slug], { replaceUrl: true });
                return false;
            } else {
                // Si no hay entidades, redirigir a la consola de super administración para configurarlas
                router.navigate(['/soft-admin'], { replaceUrl: true });
                return false;
            }
        }),
        catchError(() => {
            // En caso de error al obtener entidades, redirigir a super administración
            router.navigate(['/soft-admin'], { replaceUrl: true });
            return of(false);
        })
    );
};
