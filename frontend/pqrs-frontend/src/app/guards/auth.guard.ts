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

// Guard para portal administrativo (bloquea ciudadanos)
export const adminPortalGuard: CanActivateFn = (route, state) => {
    const authService = inject(AuthService);
    const router = inject(Router);

    if (!authService.isAuthenticated()) {
        console.log('Usuario no autenticado, redirigiendo al login administrativo');
        router.navigate(['/login']);
        return false;
    }

    // Verificar que NO sea ciudadano
    const currentUser = authService.getCurrentUserValue();
    if (currentUser && currentUser.role === 'ciudadano') {
        console.log('Ciudadano intentando acceder al portal administrativo, redirigiendo');
        router.navigate(['/portal-ciudadano']);
        return false;
    }

    // Permitir admin y secretario
    if (currentUser && (currentUser.role === 'admin' || currentUser.role === 'secretario')) {
        return true;
    }

    console.log('Rol no autorizado para portal administrativo');
    router.navigate(['/']);
    return false;
};

// Guard para portal ciudadano (bloquea admin y secretarios)
export const ciudadanoGuard: CanActivateFn = (route, state) => {
    const authService = inject(AuthService);
    const router = inject(Router);

    if (!authService.isAuthenticated()) {
        // No autenticado, permitir acceso para registro/login
        return true;
    }

    const currentUser = authService.getCurrentUserValue();
    if (currentUser && currentUser.role === 'ciudadano') {
        return true;
    }

    // Si es admin o secretario, redirigir al dashboard administrativo
    console.log('Usuario administrativo intentando acceder al portal ciudadano');
    router.navigate(['/dashboard']);
    return false;
};