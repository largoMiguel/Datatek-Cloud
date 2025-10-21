import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import {
    PQRS,
    PQRSWithDetails,
    CreatePQRSRequest,
    UpdatePQRSRequest,
    PQRSResponse,
    EstadoPQRS
} from '../models/pqrs.model';

@Injectable({
    providedIn: 'root'
})
export class PqrsService {
    private baseUrl = 'http://localhost:8000/api/pqrs/';  // Agregar barra final

    constructor(private http: HttpClient) { }

    createPqrs(pqrsData: CreatePQRSRequest): Observable<PQRS> {
        return this.http.post<PQRS>(this.baseUrl, pqrsData);
    }

    getPqrs(params?: {
        skip?: number;
        limit?: number;
        estado?: EstadoPQRS;
        assigned_to_me?: boolean;
    }): Observable<PQRSWithDetails[]> {
        let httpParams = new HttpParams();

        if (params) {
            if (params.skip !== undefined) {
                httpParams = httpParams.set('skip', params.skip.toString());
            }
            if (params.limit !== undefined) {
                httpParams = httpParams.set('limit', params.limit.toString());
            }
            if (params.estado) {
                httpParams = httpParams.set('estado', params.estado);
            }
            if (params.assigned_to_me !== undefined) {
                httpParams = httpParams.set('assigned_to_me', params.assigned_to_me.toString());
            }
        }

        return this.http.get<PQRSWithDetails[]>(this.baseUrl, { params: httpParams });
    }

    getPqrsById(id: number): Observable<PQRSWithDetails> {
        return this.http.get<PQRSWithDetails>(`${this.baseUrl}${id}`);
    }

    updatePqrs(id: number, updateData: UpdatePQRSRequest): Observable<PQRS> {
        return this.http.put<PQRS>(`${this.baseUrl}${id}`, updateData);
    }

    assignPqrs(id: number, assignedToId: number): Observable<any> {
        return this.http.post(`${this.baseUrl}${id}/assign`, { assigned_to_id: assignedToId });
    }

    respondPqrs(id: number, response: PQRSResponse): Observable<PQRS> {
        return this.http.post<PQRS>(`${this.baseUrl}${id}/respond`, response);
    }

    deletePqrs(id: number): Observable<any> {
        return this.http.delete(`${this.baseUrl}${id}`);
    }
}