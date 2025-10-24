import { Routes } from '@angular/router';
import { VentanillaComponent } from './components/ventanilla/ventanilla';
import { LoginComponent } from './components/login/login';
import { DashboardComponent } from './components/dashboard/dashboard';
import { PlanesInstitucionalesComponent } from './components/planes-institucionales/planes-institucionales';
import { PortalCiudadanoComponent } from './components/portal-ciudadano/portal-ciudadano';
import { authGuard, loginGuard, adminPortalGuard, ciudadanoGuard } from './guards/auth.guard';

export const routes: Routes = [
    { path: '', component: VentanillaComponent },
    { path: 'login', component: LoginComponent, canActivate: [loginGuard] },
    { path: 'portal-ciudadano', component: PortalCiudadanoComponent, canActivate: [ciudadanoGuard] },
    { path: 'dashboard', component: DashboardComponent, canActivate: [adminPortalGuard] },
    { path: 'planes-institucionales', component: PlanesInstitucionalesComponent, canActivate: [adminPortalGuard] },
    { path: '**', redirectTo: '' }
];