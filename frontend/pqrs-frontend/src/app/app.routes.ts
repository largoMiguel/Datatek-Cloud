import { Routes } from '@angular/router';
import { VentanillaComponent } from './components/ventanilla/ventanilla';
import { LoginComponent } from './components/login/login';
import { DashboardComponent } from './components/dashboard/dashboard';
import { PlanesInstitucionalesComponent } from './components/planes-institucionales/planes-institucionales';
import { PortalCiudadanoComponent } from './components/portal-ciudadano/portal-ciudadano';
import { SoftAdminComponent } from './components/soft-admin/soft-admin';
import { authGuard, loginGuard, adminPortalGuard, ciudadanoGuard } from './guards/auth.guard';
import { superAdminGuard } from './guards/superadmin.guard';
import { planesEnabledGuard, pqrsEnabledGuard, contratacionEnabledGuard } from './guards/feature.guard';
import { ContratacionComponent } from './components/contratacion/contratacion';
import { ensureEntityGuard } from './guards/ensure-entity.guard';
import { enforceUserEntityGuard } from './guards/enforce-user-entity.guard';
import { entityResolver } from './resolvers/entity.resolver';
import { defaultEntityGuard } from './guards/default-entity.guard';

export const routes: Routes = [
    // Ruta raíz: redirige a la primera entidad activa
    { path: '', canActivate: [defaultEntityGuard], children: [] },

    // Ruta de super administración (global, no depende de entidad)
    { path: 'soft-admin', component: SoftAdminComponent, canActivate: [superAdminGuard] },

    // Rutas por entidad (con slug). Ej: /chiquiza-boyaca/login
    {
        path: ':slug',
        canActivate: [ensureEntityGuard],
        resolve: { entity: entityResolver },
        children: [
            { path: '', component: VentanillaComponent },
            { path: 'login', component: LoginComponent, canActivate: [loginGuard] },
            { path: 'portal-ciudadano', component: PortalCiudadanoComponent, canActivate: [ciudadanoGuard, pqrsEnabledGuard] },
            { path: 'dashboard', component: DashboardComponent, canActivate: [adminPortalGuard, enforceUserEntityGuard] },
            { path: 'planes-institucionales', component: PlanesInstitucionalesComponent, canActivate: [adminPortalGuard, enforceUserEntityGuard, planesEnabledGuard] },
            { path: 'contratacion', component: ContratacionComponent, canActivate: [adminPortalGuard, enforceUserEntityGuard, contratacionEnabledGuard] },
        ]
    },
    { path: '**', redirectTo: '' }
];