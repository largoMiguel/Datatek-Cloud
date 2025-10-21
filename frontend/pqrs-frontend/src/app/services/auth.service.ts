import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Observable, BehaviorSubject, tap } from 'rxjs';
import { User, LoginRequest, LoginResponse, CreateUserRequest } from '../models/user.model';
import { environment } from '../../environments/environment.prod';

@Injectable({
    providedIn: 'root'
})
export class AuthService {
    private baseUrl = `${environment.apiUrl}/auth/`;
    private currentUserSubject = new BehaviorSubject<User | null>(null);
    public currentUser$ = this.currentUserSubject.asObservable();

    constructor(private http: HttpClient) {
        // Verificar si hay un usuario guardado en localStorage
        const savedUser = localStorage.getItem('user');
        if (savedUser) {
            this.currentUserSubject.next(JSON.parse(savedUser));
        }
    }

    login(credentials: LoginRequest): Observable<LoginResponse> {
        return this.http.post<LoginResponse>(`${this.baseUrl}login`, credentials)
            .pipe(
                tap(response => {
                    console.log('Login exitoso:', response);
                    // Guardar token y usuario
                    localStorage.setItem('token', response.access_token);
                    localStorage.setItem('user', JSON.stringify(response.user));
                    this.currentUserSubject.next(response.user);
                })
            );
    } register(userData: CreateUserRequest): Observable<User> {
        return this.http.post<User>(`${this.baseUrl}register`, userData);
    }

    logout(): void {
        console.log('Cerrando sesión...');
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        this.currentUserSubject.next(null);
    }

    getCurrentUser(): Observable<User> {
        return this.http.get<User>(`${this.baseUrl}me`);
    }

    getUsers(): Observable<User[]> {
        return this.http.get<User[]>(`${this.baseUrl}users`);
    }

    getToken(): string | null {
        const token = localStorage.getItem('token');
        console.log('Token obtenido:', token ? 'Presente' : 'No encontrado');
        return token;
    }

    isAuthenticated(): boolean {
        const token = this.getToken();
        const isAuth = !!token;
        console.log('¿Está autenticado?', isAuth);
        return isAuth;
    }

    isAdmin(): boolean {
        const user = this.currentUserSubject.value;
        return user ? user.role === 'admin' : false;
    }

    getAuthHeaders(): HttpHeaders {
        const token = this.getToken();
        return new HttpHeaders({
            'Authorization': `Bearer ${token}`
        });
    }
}