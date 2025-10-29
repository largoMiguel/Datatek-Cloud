export interface ProcesoContratacion {
    referencia_del_proceso: string;
    fase?: string;
    fecha_de_publicacion_del?: string; // ISO date
    fecha_de_ultima_publicaci?: string; // ISO date
    precio_base?: number | string;
    modalidad_de_contratacion?: string;
    duracion?: number | string;
    unidad_de_duracion?: string;
    fecha_de_recepcion_de?: string; // ISO date
    fecha_de_apertura_efectiva?: string; // ISO date
    adjudicado?: string | boolean;
    fecha_adjudicacion?: string; // ISO date
    valor_total_adjudicacion?: number | string;
    nombre_del_proveedor?: string;
    estado_de_apertura_del_proceso?: string;
    estado_resumen?: string;
    urlproceso?: string;
    descripci_n_del_procedimiento?: string;
    tipo_de_contrato?: string;
}

export interface FiltroContratacion {
    entidad?: string; // nombre en SECOP (ej: MUNICIPIO DE MOTAVITA)
    fechaDesde?: string; // YYYY-MM-DD
    fechaHasta?: string; // YYYY-MM-DD
    modalidad?: string;
    tipoContrato?: string;
    estado?: string; // estado_resumen
    adjudicado?: 'SI' | 'NO' | '';
    texto?: string; // búsqueda textual en descripción o referencia
    precioMin?: number | null;
    precioMax?: number | null;
}

export interface KPIsContratacion {
    totalProcesos: number;
    totalAdjudicados: number;
    tasaAdjudicacion: number; // 0..1
    sumaAdjudicado: number; // COP
    promedioPrecioBase: number; // COP
}
