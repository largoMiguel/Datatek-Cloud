export interface PQRS {
    id: number;
    numero_radicado: string;
    nombre_ciudadano: string;
    cedula_ciudadano: string;
    telefono_ciudadano?: string;
    email_ciudadano?: string;
    direccion_ciudadano?: string;
    tipo_solicitud: TipoSolicitud;
    asunto: string;
    descripcion: string;
    estado: EstadoPQRS;
    fecha_solicitud: string;
    fecha_cierre?: string;
    fecha_delegacion?: string;
    fecha_respuesta?: string;
    respuesta?: string;
    created_by_id: number;
    assigned_to_id?: number;
    created_at: string;
    updated_at?: string;
}

export interface PQRSWithDetails extends PQRS {
    created_by?: {
        id: number;
        username: string;
        full_name: string;
    };
    assigned_to?: {
        id: number;
        username: string;
        full_name: string;
    };
}

export interface CreatePQRSRequest {
    numero_radicado?: string;
    nombre_ciudadano: string;
    cedula_ciudadano: string;
    telefono_ciudadano?: string;
    email_ciudadano?: string;
    direccion_ciudadano?: string;
    tipo_solicitud: TipoSolicitud;
    asunto: string;
    descripcion: string;
}

export interface UpdatePQRSRequest {
    nombre_ciudadano?: string;
    cedula_ciudadano?: string;
    telefono_ciudadano?: string;
    email_ciudadano?: string;
    direccion_ciudadano?: string;
    tipo_solicitud?: TipoSolicitud;
    asunto?: string;
    descripcion?: string;
    estado?: EstadoPQRS;
    respuesta?: string;
    assigned_to_id?: number;
    fecha_solicitud?: string;
}

export interface PQRSResponse {
    respuesta: string;
}

export type TipoSolicitud = 'peticion' | 'queja' | 'reclamo' | 'sugerencia';
export type EstadoPQRS = 'pendiente' | 'en_proceso' | 'resuelto' | 'cerrado';

export const TIPOS_SOLICITUD: { value: TipoSolicitud; label: string }[] = [
    { value: 'peticion', label: 'Petición' },
    { value: 'queja', label: 'Queja' },
    { value: 'reclamo', label: 'Reclamo' },
    { value: 'sugerencia', label: 'Sugerencia' }
];

export const ESTADOS_PQRS: { value: EstadoPQRS; label: string; color: string }[] = [
    { value: 'pendiente', label: 'Pendiente', color: 'warning' },
    { value: 'en_proceso', label: 'En Proceso', color: 'info' },
    { value: 'resuelto', label: 'Resuelto', color: 'success' },
    { value: 'cerrado', label: 'Cerrado', color: 'secondary' }
];