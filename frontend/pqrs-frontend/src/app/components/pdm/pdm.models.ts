// Modelos para el PDM

export interface LineaEstrategica {
    codigoDane: string;
    entidadTerritorial: string;
    nombrePlan: string;
    consecutivo: string;
    lineaEstrategica: string;
}

export interface IndicadorResultado {
    codigoDane: string;
    entidadTerritorial: string;
    nombrePlan: string;
    consecutivo: string;
    lineaEstrategica: string;
    indicadorResultado: string;
    estaEnPND: string;
    metaCuatrienio: number;
    transformacionPND: string;
}

export interface PlanIndicativoProducto {
    codigoDane: string;
    entidadTerritorial: string;
    nombrePlan: string;
    codigoIndicador: string;
    lineaEstrategica: string;
    codigoSector: string;
    sector: string;
    codigoPrograma: string;
    programa: string;
    codigoProducto: string;
    producto: string;
    codigoIndicadorProducto: string;
    indicadorProducto: string;
    personalizacion: string;
    unidadMedida: string;
    metaCuatrienio: number;
    principal: string;
    codigoODS: string;
    ods: string;
    tipoAcumulacion: string;
    programacion2024: number;
    programacion2025: number;
    programacion2026: number;
    programacion2027: number;
    total2024: number;
    total2025: number;
    total2026: number;
    total2027: number;
    bpin?: string;
    // Estado calculado
    estado?: EstadoMeta;
    avance?: number;
    // Gestión
    secretariaAsignada?: string;
    // Avances por año registrados por el usuario
    avances?: {
        [anio: number]: {
            valor: number; // porcentaje o valor ejecutado
            comentario?: string;
        }
    };
    // Actividades para cumplimiento de la meta
    actividades?: Actividad[];
}

export interface IniciativaSGR {
    codigoDane: string;
    entidadTerritorial: string;
    nombrePlan: string;
    consecutivo: string;
    lineaEstrategica: string;
    tipoIniciativa: string;
    sector: string;
    iniciativaSGR: string;
    recursosSGR: number;
    bpin?: string;
}

export interface PlanIndicativoSGR {
    codigoDane: string;
    entidadTerritorial: string;
    nombrePlan: string;
    codigoIndicador: string;
    iniciativaSGR: string;
    codigoSector: string;
    sector: string;
    codigoPrograma: string;
    programa: string;
    codigoProducto: string;
    producto: string;
    codigoIndicadorProducto: string;
    indicadorProducto: string;
    personalizacion: string;
    unidadMedida: string;
    metaCuatrienio: number;
    principal: string;
    codigoODS: string;
    ods: string;
    tipoAcumulacion: string;
    cofinanciado: string;
    programacion20232024: number;
    programacion20252026: number;
    programacion20272028: number;
    recursosSGR20232024: number;
    recursosSGR20252026: number;
    recursosSGR20272028: number;
    bpin?: string;
}

export enum EstadoMeta {
    CUMPLIDA = 'cumplida',
    EN_PROGRESO = 'en_progreso',
    POR_CUMPLIR = 'por_cumplir',
    PENDIENTE = 'pendiente',
    SIN_DEFINIR = 'sin_definir'
}

export enum EstadoActividad {
    PENDIENTE = 'pendiente',
    EN_PROGRESO = 'en_progreso',
    COMPLETADA = 'completada',
    CANCELADA = 'cancelada'
}

export interface Actividad {
    id?: number;
    entity_id?: number;
    codigo_indicador_producto: string;
    nombre: string;
    descripcion?: string;
    responsable?: string;
    fecha_inicio?: string;  // ISO string
    fecha_fin?: string;  // ISO string
    porcentaje_avance: number;
    estado: string;
    created_at?: string;
    updated_at?: string;
}

export interface PDMData {
    lineasEstrategicas: LineaEstrategica[];
    indicadoresResultado: IndicadorResultado[];
    planIndicativoProductos: PlanIndicativoProducto[];
    iniciativasSGR: IniciativaSGR[];
    planIndicativoSGR: PlanIndicativoSGR[];
    metadata: {
        fechaCarga: Date;
        nombreArchivo: string;
        totalRegistros: number;
    };
}

export interface AnalisisPDM {
    indicadoresGenerales: {
        totalMetas: number;
        metasCumplidas: number;
        metasEnProgreso: number;
        metasPorCumplir: number;
        metasPendientes: number;
        porcentajeCumplimiento: number;
    };
    analisisPorAnio: {
        anio: number;
        totalMetas: number;
        metasCumplidas: number;
        porcentajeCumplimiento: number;
        presupuestoTotal: number;
    }[];
    analisisPorSector: {
        sector: string;
        totalMetas: number;
        metasCumplidas: number;
        porcentajeCumplimiento: number;
        presupuestoTotal: number;
    }[];
    analisisPorLineaEstrategica: {
        lineaEstrategica: string;
        totalMetas: number;
        metasCumplidas: number;
        porcentajeCumplimiento: number;
    }[];
    tendencias: {
        descripcion: string;
        tipo: 'positivo' | 'neutro' | 'negativo';
    }[];
    recomendaciones: string[];
    alertas: string[];
    inconsistencias: {
        tipo: string;
        descripcion: string;
        cantidad: number;
    }[];
}

export interface FiltrosPDM {
    anio?: number;
    sector?: string;
    lineaEstrategica?: string;
    estado?: EstadoMeta;
    secretaria?: string;
}
