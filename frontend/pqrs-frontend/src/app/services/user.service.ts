import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { User } from '../models/user.model';
import { environment } from '../../environments/environment';

@Injectable({
    providedIn: 'root'
})
export class UserService {
    private baseUrl = `${environment.apiUrl}/users/`;

    constructor(private http: HttpClient) { }

    getUsers(): Observable<User[]> {
        return this.http.get<User[]>(this.baseUrl);
    }

    getUser(id: number): Observable<User> {
        return this.http.get<User>(`${this.baseUrl}${id}/`);
    }

    createUser(userData: any): Observable<User> {
        return this.http.post<User>(this.baseUrl, userData);
    }

    updateUser(id: number, userData: any): Observable<User> {
        return this.http.put<User>(`${this.baseUrl}${id}/`, userData);
    }

    deleteUser(id: number): Observable<any> {
        return this.http.delete(`${this.baseUrl}${id}/`);
    }

    toggleUserStatus(id: number): Observable<User> {
        return this.http.patch<User>(`${this.baseUrl}${id}/toggle-status/`, {});
    }

    getSecretarios(): Observable<User[]> {
        return this.http.get<User[]>(`${this.baseUrl}?role=secretario`);
    }

    changeUserPassword(id: number, newPassword: string): Observable<{ message: string }> {
        return this.http.post<{ message: string }>(`${this.baseUrl}${id}/change-password/`, { new_password: newPassword });
    }
}