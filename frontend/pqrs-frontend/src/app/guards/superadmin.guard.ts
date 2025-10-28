import { inject } from '@angular/core';
import { Router, CanActivateFn } from '@angular/router';
import { AuthService } from '../services/auth.service';
import { AlertService } from '../services/alert.service';
import { EntityContextService } from '../services/entity-context.service';

export const superAdminGuard: CanActivateFn = (route, state) => {
    const authService = inject(AuthService);
    const router = inject(Router);
    const alertService = inject(AlertService);
    const entityContext = inject(EntityContextService);

    const currentUser = authService.getCurrentUserValue();

    if (!currentUser) {
        alertService.error('Debes iniciar sesión');
        const slug = route.params?.['slug'] || route.parent?.params?.['slug'] || entityContext.currentEntity?.slug || null;
        router.navigate(slug ? ['/', slug, 'login'] : ['/']);
        return false;
    }

    if (currentUser.role !== 'superadmin') {
        alertService.error('Acceso denegado. Se requieren permisos de super administrador.');
        const slug = route.params?.['slug'] || route.parent?.params?.['slug'] || entityContext.currentEntity?.slug || null;
        router.navigate(slug ? ['/', slug, 'dashboard'] : ['/']);
        return false;
    }

    return true;
};
