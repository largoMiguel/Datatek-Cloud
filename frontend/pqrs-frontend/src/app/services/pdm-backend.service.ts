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
}
