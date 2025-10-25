import { CanActivateFn, Router } from '@angular/router';
import { inject } from '@angular/core';
import { AuthService } from '../services/auth.service';

export const authGuard: CanActivateFn = (route, state) => {
    const authService = inject(AuthService);
    const router = inject(Router);

    if (authService.isAuthenticated()) {
        return true;
    } else {
        router.navigate(['/login']);
        return false;
    }
};

export const loginGuard: CanActivateFn = (route, state) => {
    const authService = inject(AuthService);
    const router = inject(Router);

    if (authService.isAuthenticated()) {
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
        router.navigate(['/dashboard']);
        return false;
    }
};

export const adminPortalGuard: CanActivateFn = (route, state) => {
    const authService = inject(AuthService);
    const router = inject(Router);

    if (!authService.isAuthenticated()) {
        router.navigate(['/login']);
        return false;
    }

    const currentUser = authService.getCurrentUserValue();
    if (currentUser && currentUser.role === 'ciudadano') {
        router.navigate(['/portal-ciudadano']);
        return false;
    }

    if (currentUser && (currentUser.role === 'admin' || currentUser.role === 'secretario')) {
        return true;
    }

    router.navigate(['/']);
    return false;
};

export const ciudadanoGuard: CanActivateFn = (route, state) => {
    const authService = inject(AuthService);
    const router = inject(Router);

    if (!authService.isAuthenticated()) {
        return true;
    }

    const currentUser = authService.getCurrentUserValue();
    if (currentUser && currentUser.role === 'ciudadano') {
        return true;
    }

    router.navigate(['/dashboard']);
    return false;
};