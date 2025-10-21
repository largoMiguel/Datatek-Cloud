import { CanActivateFn, Router } from '@angular/router';
import { inject } from '@angular/core';
import { AuthService } from '../services/auth.service';

export const authGuard: CanActivateFn = (route, state) => {
    const authService = inject(AuthService);
    const router = inject(Router);

    if (authService.isAuthenticated()) {
        return true;
    } else {
        console.log('Usuario no autenticado, redirigiendo al login');
        router.navigate(['/login']);
        return false;
    }
};

export const loginGuard: CanActivateFn = (route, state) => {
    const authService = inject(AuthService);
    const router = inject(Router);

    // Si ya está autenticado, redirigir al dashboard
    if (authService.isAuthenticated()) {
        console.log('Usuario ya autenticado, redirigiendo al dashboard');
        router.navigate(['/dashboard'], { replaceUrl: true });
        return false;
    }
    return true;
};

export const adminGuard: CanActivateFn = (route, state) => {
    const authService = inject(AuthService);
    const router = inject(Router);

    if (authService.isAuthenticated() && authService.isAdmin()) {
        return true;
    } else {
        console.log('Usuario no es admin, redirigiendo al dashboard');
        router.navigate(['/dashboard']);
        return false;
    }
};