export interface User {
    id: number;
    username: string;
    email: string;
    full_name: string;
    role: 'admin' | 'secretario' | 'ciudadano';
    is_active?: boolean;
    secretaria?: string;
    cedula?: string;
    telefono?: string;
    direccion?: string;
    created_at?: string;
    updated_at?: string;
}

export interface LoginRequest {
    username: string;
    password: string;
}

export interface LoginResponse {
    access_token: string;
    token_type: string;
    user: User;
}

export interface CreateUserRequest {
    username: string;
    email: string;
    full_name: string;
    role: 'admin' | 'secretario' | 'ciudadano';
    secretaria?: string;
    cedula?: string;
    telefono?: string;
    direccion?: string;
    password: string;
}