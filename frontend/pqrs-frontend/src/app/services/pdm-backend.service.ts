import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface AssignmentUpsertRequest {
    codigo_indicador_producto: string;
    secretaria?: string | null;
}

export interface AssignmentMapResponse {
    assignments: Record<string, string | null>;
}

export interface AvanceUpsertRequest {
    codigo_indicador_producto: string;
    anio: number;
    valor_ejecutado: number;
    comentario?: string;
}

export interface AvanceResponse {
    entity_id: number;
    codigo_indicador_producto: string;
    anio: number;
    valor_ejecutado: number;
    comentario?: string;
}

export interface ActividadCreateRequest {
    codigo_indicador_producto: string;
    nombre: string;
    descripcion?: string;
    responsable?: string;
    fecha_inicio?: string;
    fecha_fin?: string;
    porcentaje_avance: number;
    estado: string;
}

export interface ActividadUpdateRequest {
    nombre?: string;
    descripcion?: string;
    responsable?: string;
    fecha_inicio?: string;
    fecha_fin?: string;
    porcentaje_avance?: number;
    estado?: string;
}

export interface ActividadResponse {
    id: number;
    entity_id: number;
    codigo_indicador_producto: string;
    nombre: string;
    descripcion?: string;
    responsable?: string;
    fecha_inicio?: string;
    fecha_fin?: string;
    porcentaje_avance: number;
    estado: string;
    created_at: string;
    updated_at: string;
}

@Injectable({ providedIn: 'root' })
export class PdmBackendService {
    private http = inject(HttpClient);
    private baseUrl = `${environment.apiUrl}/pdm`;

    getAssignments(slug: string): Observable<AssignmentMapResponse> {
        return this.http.get<AssignmentMapResponse>(`${this.baseUrl}/${slug}/assignments`);
    }

    upsertAssignment(slug: string, payload: AssignmentUpsertRequest): Observable<any> {
        return this.http.post(`${this.baseUrl}/${slug}/assignments`, payload);
    }

    getAvances(slug: string, codigo: string): Observable<{ codigo_indicador_producto: string; avances: AvanceResponse[] }> {
        return this.http.get<{ codigo_indicador_producto: string; avances: AvanceResponse[] }>(`${this.baseUrl}/${slug}/avances`, { params: { codigo } });
    }

    upsertAvance(slug: string, payload: AvanceUpsertRequest): Observable<AvanceResponse> {
        return this.http.post<AvanceResponse>(`${this.baseUrl}/${slug}/avances`, payload);
    }

    getActividades(slug: string, codigo: string): Observable<{ codigo_indicador_producto: string; actividades: ActividadResponse[] }> {
        return this.http.get<{ codigo_indicador_producto: string; actividades: ActividadResponse[] }>(`${this.baseUrl}/${slug}/actividades`, { params: { codigo } });
    }

    createActividad(slug: string, payload: ActividadCreateRequest): Observable<ActividadResponse> {
        return this.http.post<ActividadResponse>(`${this.baseUrl}/${slug}/actividades`, payload);
    }

    updateActividad(slug: string, actividadId: number, payload: ActividadUpdateRequest): Observable<ActividadResponse> {
        return this.http.put<ActividadResponse>(`${this.baseUrl}/${slug}/actividades/${actividadId}`, payload);
    }

    deleteActividad(slug: string, actividadId: number): Observable<void> {
        return this.http.delete<void>(`${this.baseUrl}/${slug}/actividades/${actividadId}`);
    }
}
