import { Injectable } from '@angular/core';
import { HttpInterceptor, HttpRequest, HttpHandler, HttpEvent } from '@angular/common/http';
import { Observable, catchError, throwError } from 'rxjs';
import { AuthService } from '../services/auth.service';
import { Router } from '@angular/router';
import { EntityContextService } from '../services/entity-context.service';

@Injectable()
export class AuthInterceptor implements HttpInterceptor {
    constructor(
        private authService: AuthService,
        private router: Router,
        private entityContext: EntityContextService
    ) { }

    intercept(req: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
        const token = this.authService.getToken();

        if (token) {
            const authReq = req.clone({
                setHeaders: {
                    Authorization: `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            return next.handle(authReq).pipe(
                catchError(error => {
                    if (error.status === 401) {
                        this.authService.logout();
                        const currentUrl = this.router.url;
                        const slug = (currentUrl || '').replace(/^\//, '').split('/')[0] || this.entityContext.currentEntity?.slug || null;
                        this.router.navigate(slug ? ['/', slug, 'login'] : ['/']);
                    }
                    return throwError(() => error);
                })
            );
        }

        return next.handle(req);
    }
}