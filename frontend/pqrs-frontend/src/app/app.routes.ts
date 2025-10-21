import { Routes } from '@angular/router';
import { LoginComponent } from './components/login/login';
import { DashboardComponent } from './components/dashboard/dashboard';
import { PlanesInstitucionalesComponent } from './components/planes-institucionales/planes-institucionales';
import { authGuard, loginGuard } from './guards/auth.guard';

export const routes: Routes = [
    { path: '', component: LoginComponent, canActivate: [loginGuard] },
    { path: 'login', component: LoginComponent, canActivate: [loginGuard] },
    { path: 'dashboard', component: DashboardComponent, canActivate: [authGuard] },
    { path: 'planes-institucionales', component: PlanesInstitucionalesComponent, canActivate: [authGuard] },
    { path: '**', redirectTo: '' }
];