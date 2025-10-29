import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';

/**
 * Guard para proteger rutas según los módulos asignados al usuario.
 * Verifica que el usuario tenga acceso al módulo específico antes de permitir la navegación.
 * 
 * Uso: canActivate: [moduleAccessGuard('pqrs')]
 */
export const moduleAccessGuard = (requiredModule: string): CanActivateFn => {
    return () => {
        const authService = inject(AuthService);
        const router = inject(Router);

        const currentUser = authService.getCurrentUserValue();

        if (!currentUser) {
            router.navigate(['/login']);
            return false;
        }

        // ADMIN siempre tiene acceso
        if (currentUser.role === 'admin' || currentUser.role === 'superadmin') {
            return true;
        }        // Si el usuario no tiene allowed_modules definido (null o undefined),
        // es un usuario legacy con acceso completo (comportamiento anterior)
        if (!currentUser.allowed_modules) {
            return true;
        }

        // Si tiene allowed_modules vacío, no tiene acceso a nada
        if (currentUser.allowed_modules.length === 0) {
            router.navigate(['/dashboard']);
            return false;
        }

        // Verificar si el usuario tiene el módulo requerido
        const hasAccess = currentUser.allowed_modules.includes(requiredModule);

        if (!hasAccess) {
            router.navigate(['/dashboard']);
            return false;
        }

        return true;
    };
};