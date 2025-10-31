import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';
import * as XLSX from 'xlsx';
import {
    PDMData,
    AnalisisPDM,
    LineaEstrategica,
    IndicadorResultado,
    PlanIndicativoProducto,
    IniciativaSGR,
    PlanIndicativoSGR,
    EstadoMeta,
    FiltrosPDM
} from './pdm.models';

@Injectable({
    providedIn: 'root'
})
export class PdmDataService {
    private readonly CACHE_KEY = 'pdm_data_cache';
    private readonly CACHE_VERSION = '1.0.0';
    private readonly CACHE_EXPIRATION_DAYS = 30;

    private pdmDataSubject = new BehaviorSubject<PDMData | null>(null);
    private analisisSubject = new BehaviorSubject<AnalisisPDM | null>(null);
    private cargandoSubject = new BehaviorSubject<boolean>(false);

    pdmData$ = this.pdmDataSubject.asObservable();
    analisis$ = this.analisisSubject.asObservable();
    cargando$ = this.cargandoSubject.asObservable();

    constructor() {
        this.cargarDatosDesdCache();
    }

    /**
     * Carga los datos desde el caché si existen y son válidos
     */
    private cargarDatosDesdCache(): void {
        try {
            const cacheString = localStorage.getItem(this.CACHE_KEY);
            if (!cacheString) return;

            const cache = JSON.parse(cacheString);

            // Validar versión
            if (cache.version !== this.CACHE_VERSION) {
                this.limpiarCache();
                return;
            }

            // Validar expiración
            const fechaCache = new Date(cache.timestamp);
            const fechaActual = new Date();
            const diasDiferencia = Math.floor((fechaActual.getTime() - fechaCache.getTime()) / (1000 * 60 * 60 * 24));

            if (diasDiferencia > this.CACHE_EXPIRATION_DAYS) {
                this.limpiarCache();
                return;
            }

            // Cargar datos
            if (cache.pdmData && cache.analisis) {
                // Recalcular estados según fecha actual
                this.calcularEstadosYAvances(cache.pdmData);

                this.pdmDataSubject.next(cache.pdmData);
                this.analisisSubject.next(cache.analisis);
            }
        } catch (error) {
            console.error('Error al cargar datos desde caché:', error);
            this.limpiarCache();
        }
    }

    /**
     * Guarda los datos en el caché
     */
    private guardarDatosEnCache(pdmData: PDMData, analisis: AnalisisPDM): void {
        try {
            const cache = {
                version: this.CACHE_VERSION,
                timestamp: new Date().toISOString(),
                pdmData,
                analisis
            };
            localStorage.setItem(this.CACHE_KEY, JSON.stringify(cache));
        } catch (error) {
            console.error('Error al guardar datos en caché:', error);
            // Si el localStorage está lleno, limpiar y reintentar
            this.limpiarCache();
            try {
                const cache = {
                    version: this.CACHE_VERSION,
                    timestamp: new Date().toISOString(),
                    pdmData,
                    analisis
                };
                localStorage.setItem(this.CACHE_KEY, JSON.stringify(cache));
            } catch (retryError) {
                console.error('Error al guardar datos en caché (reintento):', retryError);
            }
        }
    }

    /**
     * Limpia el caché
     */
    private limpiarCache(): void {
        localStorage.removeItem(this.CACHE_KEY);
    }

    /**
     * Obtiene información del caché actual
     */
    obtenerInfoCache(): { existe: boolean; fecha?: Date; version?: string } {
        try {
            const cacheString = localStorage.getItem(this.CACHE_KEY);
            if (!cacheString) return { existe: false };

            const cache = JSON.parse(cacheString);
            return {
                existe: true,
                fecha: new Date(cache.timestamp),
                version: cache.version
            };
        } catch (error) {
            return { existe: false };
        }
    }

    /**
     * Verifica si hay datos en caché
     */
    tieneDatosEnCache(): boolean {
        return this.pdmDataSubject.value !== null;
    }

    /**
     * Procesa un archivo Excel con las 5 hojas del PDM
     */
    procesarArchivoExcel(file: File): Promise<PDMData> {
        return new Promise((resolve, reject) => {
            this.cargandoSubject.next(true);

            const reader = new FileReader();

            reader.onload = (e: any) => {
                try {
                    const data = new Uint8Array(e.target.result);
                    const workbook = XLSX.read(data, { type: 'array' });

                    // Validar que existan las hojas necesarias
                    const hojasRequeridas = [
                        'Líneas estratégicas',
                        'Indicadores de resultado',
                        'Plan indicativo - Productos',
                        'Iniciativas SGR',
                        'Plan indicativo SGR - Produc'
                    ];

                    const pdmData: PDMData = {
                        lineasEstrategicas: this.procesarLineasEstrategicas(workbook),
                        indicadoresResultado: this.procesarIndicadoresResultado(workbook),
                        planIndicativoProductos: this.procesarPlanIndicativoProductos(workbook),
                        iniciativasSGR: this.procesarIniciativasSGR(workbook),
                        planIndicativoSGR: this.procesarPlanIndicativoSGR(workbook),
                        metadata: {
                            fechaCarga: new Date(),
                            nombreArchivo: file.name,
                            totalRegistros: 0
                        }
                    };

                    // Calcular total de registros
                    pdmData.metadata.totalRegistros =
                        pdmData.lineasEstrategicas.length +
                        pdmData.indicadoresResultado.length +
                        pdmData.planIndicativoProductos.length +
                        pdmData.iniciativasSGR.length +
                        pdmData.planIndicativoSGR.length;

                    // Calcular estados y avances
                    this.calcularEstadosYAvances(pdmData);

                    // Actualizar sujetos
                    this.pdmDataSubject.next(pdmData);

                    // Generar análisis
                    const analisis = this.generarAnalisis(pdmData);
                    this.analisisSubject.next(analisis);

                    // Guardar en caché
                    this.guardarDatosEnCache(pdmData, analisis);

                    this.cargandoSubject.next(false);
                    resolve(pdmData);
                } catch (error) {
                    this.cargandoSubject.next(false);
                    reject(error);
                }
            };

            reader.onerror = (error) => {
                this.cargandoSubject.next(false);
                reject(error);
            };

            reader.readAsArrayBuffer(file);
        });
    }

    private procesarLineasEstrategicas(workbook: XLSX.WorkBook): LineaEstrategica[] {
        const nombreHoja = this.encontrarHoja(workbook, ['Líneas estratégicas', 'LÍNEAS ESTRATÉGICAS', 'Lineas estrategicas']);
        if (!nombreHoja) return [];

        const worksheet = workbook.Sheets[nombreHoja];
        const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1 });

        return this.mapearDatos(jsonData, (row: any[]) => ({
            codigoDane: this.limpiarValor(row[0]),
            entidadTerritorial: this.limpiarValor(row[1]),
            nombrePlan: this.limpiarValor(row[2]),
            consecutivo: this.limpiarValor(row[3]),
            lineaEstrategica: this.limpiarValor(row[4])
        }));
    }

    private procesarIndicadoresResultado(workbook: XLSX.WorkBook): IndicadorResultado[] {
        const nombreHoja = this.encontrarHoja(workbook, ['Indicadores de resultado', 'INDICADORES DE RESULTADO']);
        if (!nombreHoja) return [];

        const worksheet = workbook.Sheets[nombreHoja];
        const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1 });

        return this.mapearDatos(jsonData, (row: any[]) => ({
            codigoDane: this.limpiarValor(row[0]),
            entidadTerritorial: this.limpiarValor(row[1]),
            nombrePlan: this.limpiarValor(row[2]),
            consecutivo: this.limpiarValor(row[3]),
            lineaEstrategica: this.limpiarValor(row[4]),
            indicadorResultado: this.limpiarValor(row[5]),
            estaEnPND: this.limpiarValor(row[6]),
            metaCuatrienio: this.convertirNumero(row[7]),
            transformacionPND: this.limpiarValor(row[8])
        }));
    }

    private procesarPlanIndicativoProductos(workbook: XLSX.WorkBook): PlanIndicativoProducto[] {
        const nombreHoja = this.encontrarHoja(workbook, ['Plan indicativo - Productos', 'PLAN INDICATIVO', 'Plan indicativo']);
        if (!nombreHoja) return [];

        const worksheet = workbook.Sheets[nombreHoja];
        const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1 });

        return this.mapearDatos(jsonData, (row: any[]) => ({
            codigoDane: this.limpiarValor(row[0]),
            entidadTerritorial: this.limpiarValor(row[1]),
            nombrePlan: this.limpiarValor(row[2]),
            codigoIndicador: this.limpiarValor(row[3]),
            lineaEstrategica: this.limpiarValor(row[4]),
            codigoSector: this.limpiarValor(row[5]),
            sector: this.limpiarValor(row[6]),
            codigoPrograma: this.limpiarValor(row[7]),
            programa: this.limpiarValor(row[8]),
            codigoProducto: this.limpiarValor(row[9]),
            producto: this.limpiarValor(row[10]),
            codigoIndicadorProducto: this.limpiarValor(row[11]),
            indicadorProducto: this.limpiarValor(row[12]),
            personalizacion: this.limpiarValor(row[13]),
            unidadMedida: this.limpiarValor(row[14]),
            metaCuatrienio: this.convertirNumero(row[15]),
            principal: this.limpiarValor(row[16]),
            codigoODS: this.limpiarValor(row[17]),
            ods: this.limpiarValor(row[18]),
            tipoAcumulacion: this.limpiarValor(row[19]),
            programacion2024: this.convertirNumero(row[20]),
            programacion2025: this.convertirNumero(row[21]),
            programacion2026: this.convertirNumero(row[22]),
            programacion2027: this.convertirNumero(row[23]),
            total2024: this.convertirNumero(row[38]),
            total2025: this.convertirNumero(row[53]),
            total2026: this.convertirNumero(row[68]),
            total2027: this.convertirNumero(row[83]),
            bpin: this.limpiarValor(row[84])
        }));
    }

    private procesarIniciativasSGR(workbook: XLSX.WorkBook): IniciativaSGR[] {
        const nombreHoja = this.encontrarHoja(workbook, ['Iniciativas SGR', 'INICIATIVAS SGR']);
        if (!nombreHoja) return [];

        const worksheet = workbook.Sheets[nombreHoja];
        const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1 });

        return this.mapearDatos(jsonData, (row: any[]) => ({
            codigoDane: this.limpiarValor(row[0]),
            entidadTerritorial: this.limpiarValor(row[1]),
            nombrePlan: this.limpiarValor(row[2]),
            consecutivo: this.limpiarValor(row[3]),
            lineaEstrategica: this.limpiarValor(row[4]),
            tipoIniciativa: this.limpiarValor(row[5]),
            sector: this.limpiarValor(row[6]),
            iniciativaSGR: this.limpiarValor(row[7]),
            recursosSGR: this.convertirNumero(row[8]),
            bpin: this.limpiarValor(row[9])
        }));
    }

    private procesarPlanIndicativoSGR(workbook: XLSX.WorkBook): PlanIndicativoSGR[] {
        const nombreHoja = this.encontrarHoja(workbook, ['Plan indicativo SGR - Produc', 'Plan indicativo SGR', 'PLAN INDICATIVO SGR']);
        if (!nombreHoja) return [];

        const worksheet = workbook.Sheets[nombreHoja];
        const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1 });

        return this.mapearDatos(jsonData, (row: any[]) => ({
            codigoDane: this.limpiarValor(row[0]),
            entidadTerritorial: this.limpiarValor(row[1]),
            nombrePlan: this.limpiarValor(row[2]),
            codigoIndicador: this.limpiarValor(row[3]),
            iniciativaSGR: this.limpiarValor(row[4]),
            codigoSector: this.limpiarValor(row[5]),
            sector: this.limpiarValor(row[6]),
            codigoPrograma: this.limpiarValor(row[7]),
            programa: this.limpiarValor(row[8]),
            codigoProducto: this.limpiarValor(row[9]),
            producto: this.limpiarValor(row[10]),
            codigoIndicadorProducto: this.limpiarValor(row[11]),
            indicadorProducto: this.limpiarValor(row[12]),
            personalizacion: this.limpiarValor(row[13]),
            unidadMedida: this.limpiarValor(row[14]),
            metaCuatrienio: this.convertirNumero(row[15]),
            principal: this.limpiarValor(row[16]),
            codigoODS: this.limpiarValor(row[17]),
            ods: this.limpiarValor(row[18]),
            tipoAcumulacion: this.limpiarValor(row[19]),
            cofinanciado: this.limpiarValor(row[20]),
            programacion20232024: this.convertirNumero(row[21]),
            programacion20252026: this.convertirNumero(row[22]),
            programacion20272028: this.convertirNumero(row[23]),
            recursosSGR20232024: this.convertirNumero(row[24]),
            recursosSGR20252026: this.convertirNumero(row[25]),
            recursosSGR20272028: this.convertirNumero(row[26]),
            bpin: this.limpiarValor(row[27])
        }));
    }

    private calcularEstadosYAvances(pdmData: PDMData): void {
        const añoActual = new Date().getFullYear();

        pdmData.planIndicativoProductos.forEach(producto => {
            const totalProgramado =
                producto.programacion2024 +
                producto.programacion2025 +
                producto.programacion2026 +
                producto.programacion2027;

            let totalEjecutado = 0;

            // Calcular ejecutado basado en el año actual
            if (añoActual >= 2024) totalEjecutado += producto.programacion2024;
            if (añoActual >= 2025) totalEjecutado += producto.programacion2025;
            if (añoActual >= 2026) totalEjecutado += producto.programacion2026;
            if (añoActual >= 2027) totalEjecutado += producto.programacion2027;

            // Calcular avance
            producto.avance = totalProgramado > 0 ? (totalEjecutado / totalProgramado) * 100 : 0;

            // Determinar estado
            if (producto.avance >= 100) {
                producto.estado = EstadoMeta.CUMPLIDA;
            } else if (producto.avance >= 50) {
                producto.estado = EstadoMeta.EN_PROGRESO;
            } else if (producto.avance > 0) {
                producto.estado = EstadoMeta.PENDIENTE;
            } else {
                producto.estado = EstadoMeta.POR_CUMPLIR;
            }
        });
    }

    private generarAnalisis(pdmData: PDMData): AnalisisPDM {
        const productos = pdmData.planIndicativoProductos;

        // Indicadores generales
        const totalMetas = productos.length;
        const metasCumplidas = productos.filter(p => p.estado === EstadoMeta.CUMPLIDA).length;
        const metasEnProgreso = productos.filter(p => p.estado === EstadoMeta.EN_PROGRESO).length;
        const metasPorCumplir = productos.filter(p => p.estado === EstadoMeta.POR_CUMPLIR).length;
        const metasPendientes = productos.filter(p => p.estado === EstadoMeta.PENDIENTE).length;
        const porcentajeCumplimiento = totalMetas > 0 ? (metasCumplidas / totalMetas) * 100 : 0;

        // Análisis por año
        const analisisPorAnio = [2024, 2025, 2026, 2027].map(anio => {
            const metasAnio = productos.filter(p => {
                const prog = anio === 2024 ? p.programacion2024 :
                    anio === 2025 ? p.programacion2025 :
                        anio === 2026 ? p.programacion2026 :
                            p.programacion2027;
                return prog > 0;
            });

            const presupuestoTotal = productos.reduce((sum, p) => {
                const total = anio === 2024 ? p.total2024 :
                    anio === 2025 ? p.total2025 :
                        anio === 2026 ? p.total2026 :
                            p.total2027;
                return sum + total;
            }, 0);

            return {
                anio,
                totalMetas: metasAnio.length,
                metasCumplidas: metasAnio.filter(p => p.estado === EstadoMeta.CUMPLIDA).length,
                porcentajeCumplimiento: metasAnio.length > 0
                    ? (metasAnio.filter(p => p.estado === EstadoMeta.CUMPLIDA).length / metasAnio.length) * 100
                    : 0,
                presupuestoTotal
            };
        });

        // Análisis por sector
        const sectoresUnicos = [...new Set(productos.map(p => p.sector))].filter(s => s);
        const analisisPorSector = sectoresUnicos.map(sector => {
            const metasSector = productos.filter(p => p.sector === sector);
            const cumplidas = metasSector.filter(p => p.estado === EstadoMeta.CUMPLIDA).length;
            const presupuestoTotal = metasSector.reduce((sum, p) =>
                sum + p.total2024 + p.total2025 + p.total2026 + p.total2027, 0);

            return {
                sector,
                totalMetas: metasSector.length,
                metasCumplidas: cumplidas,
                porcentajeCumplimiento: metasSector.length > 0 ? (cumplidas / metasSector.length) * 100 : 0,
                presupuestoTotal
            };
        }).sort((a, b) => b.porcentajeCumplimiento - a.porcentajeCumplimiento);

        // Análisis por línea estratégica
        const lineasUnicas = [...new Set(productos.map(p => p.lineaEstrategica))].filter(l => l);
        const analisisPorLineaEstrategica = lineasUnicas.map(linea => {
            const metasLinea = productos.filter(p => p.lineaEstrategica === linea);
            const cumplidas = metasLinea.filter(p => p.estado === EstadoMeta.CUMPLIDA).length;

            return {
                lineaEstrategica: linea,
                totalMetas: metasLinea.length,
                metasCumplidas: cumplidas,
                porcentajeCumplimiento: metasLinea.length > 0 ? (cumplidas / metasLinea.length) * 100 : 0
            };
        }).sort((a, b) => b.porcentajeCumplimiento - a.porcentajeCumplimiento);

        // Generar tendencias
        const tendencias = this.generarTendencias(analisisPorAnio, analisisPorSector);

        // Generar recomendaciones
        const recomendaciones = this.generarRecomendaciones(
            porcentajeCumplimiento,
            analisisPorSector,
            analisisPorLineaEstrategica
        );

        // Generar alertas
        const alertas = this.generarAlertas(analisisPorSector, analisisPorAnio);

        // Detectar inconsistencias
        const inconsistencias = this.detectarInconsistencias(pdmData);

        return {
            indicadoresGenerales: {
                totalMetas,
                metasCumplidas,
                metasEnProgreso,
                metasPorCumplir,
                metasPendientes,
                porcentajeCumplimiento
            },
            analisisPorAnio,
            analisisPorSector,
            analisisPorLineaEstrategica,
            tendencias,
            recomendaciones,
            alertas,
            inconsistencias
        };
    }

    private generarTendencias(
        analisisPorAnio: any[],
        analisisPorSector: any[]
    ): { descripcion: string; tipo: 'positivo' | 'neutro' | 'negativo' }[] {
        const tendencias: { descripcion: string; tipo: 'positivo' | 'neutro' | 'negativo' }[] = [];

        // Tendencia general por años
        const cumplimientos = analisisPorAnio.map(a => a.porcentajeCumplimiento);
        let tendenciaGeneral = 0;
        for (let i = 1; i < cumplimientos.length; i++) {
            tendenciaGeneral += cumplimientos[i] - cumplimientos[i - 1];
        }

        if (tendenciaGeneral > 0) {
            tendencias.push({
                descripcion: `Se observa una tendencia positiva en el cumplimiento de metas a lo largo del cuatrienio, con un incremento promedio de ${(tendenciaGeneral / (cumplimientos.length - 1)).toFixed(1)}% anual.`,
                tipo: 'positivo'
            });
        } else if (tendenciaGeneral < 0) {
            tendencias.push({
                descripcion: `Se identifica una tendencia negativa en el cumplimiento, con una disminución promedio de ${Math.abs(tendenciaGeneral / (cumplimientos.length - 1)).toFixed(1)}% anual.`,
                tipo: 'negativo'
            });
        }

        // Mejor sector
        if (analisisPorSector.length > 0) {
            const mejorSector = analisisPorSector[0];
            tendencias.push({
                descripcion: `El sector "${mejorSector.sector}" presenta el mejor desempeño con un ${mejorSector.porcentajeCumplimiento.toFixed(1)}% de cumplimiento.`,
                tipo: 'positivo'
            });

            // Peor sector (si existe)
            const peorSector = analisisPorSector[analisisPorSector.length - 1];
            if (peorSector.porcentajeCumplimiento < 50) {
                tendencias.push({
                    descripcion: `El sector "${peorSector.sector}" requiere atención especial, con solo un ${peorSector.porcentajeCumplimiento.toFixed(1)}% de cumplimiento.`,
                    tipo: 'negativo'
                });
            }
        }

        return tendencias;
    }

    private generarRecomendaciones(
        porcentajeGeneral: number,
        analisisPorSector: any[],
        analisisPorLinea: any[]
    ): string[] {
        const recomendaciones: string[] = [];

        if (porcentajeGeneral < 50) {
            recomendaciones.push(
                'El porcentaje de cumplimiento general es bajo. Se recomienda realizar una evaluación exhaustiva de los factores que están impidiendo el avance de las metas programadas.'
            );
        }

        // Sectores con bajo cumplimiento
        const sectoresBajos = analisisPorSector.filter(s => s.porcentajeCumplimiento < 40);
        if (sectoresBajos.length > 0) {
            recomendaciones.push(
                `Se identificaron ${sectoresBajos.length} sector(es) con cumplimiento inferior al 40%. Se sugiere priorizar recursos y atención en: ${sectoresBajos.map(s => s.sector).join(', ')}.`
            );
        }

        // Líneas estratégicas rezagadas
        const lineasRezagadas = analisisPorLinea.filter(l => l.porcentajeCumplimiento < 30);
        if (lineasRezagadas.length > 0) {
            recomendaciones.push(
                `Existen líneas estratégicas con avance crítico. Se recomienda reevaluar la viabilidad y pertinencia de las metas asociadas.`
            );
        }

        // Recomendación positiva
        const sectoresAltos = analisisPorSector.filter(s => s.porcentajeCumplimiento >= 70);
        if (sectoresAltos.length > 0) {
            recomendaciones.push(
                `Se destacan ${sectoresAltos.length} sector(es) con cumplimiento superior al 70%. Se sugiere documentar las buenas prácticas implementadas para replicarlas en otros sectores.`
            );
        }

        return recomendaciones;
    }

    private generarAlertas(analisisPorSector: any[], analisisPorAnio: any[]): string[] {
        const alertas: string[] = [];

        // Alertas por sector crítico
        const sectoresCriticos = analisisPorSector.filter(s => s.porcentajeCumplimiento < 25);
        sectoresCriticos.forEach(sector => {
            alertas.push(
                `⚠️ CRÍTICO: El sector "${sector.sector}" presenta un cumplimiento del ${sector.porcentajeCumplimiento.toFixed(1)}%. Se requiere intervención inmediata.`
            );
        });

        // Alertas por año con bajo presupuesto ejecutado
        const anioActual = new Date().getFullYear();
        const añosAnteriores = analisisPorAnio.filter(a => a.anio < anioActual);
        añosAnteriores.forEach(anio => {
            if (anio.porcentajeCumplimiento < 50) {
                alertas.push(
                    `⚠️ El año ${anio.anio} cerró con un cumplimiento del ${anio.porcentajeCumplimiento.toFixed(1)}%. Esto puede comprometer las metas del cuatrienio.`
                );
            }
        });

        return alertas;
    }

    private detectarInconsistencias(pdmData: PDMData): any[] {
        const inconsistencias: any[] = [];

        // Productos sin sector
        const sinSector = pdmData.planIndicativoProductos.filter(p => !p.sector || p.sector.trim() === '');
        if (sinSector.length > 0) {
            inconsistencias.push({
                tipo: 'Productos sin sector definido',
                descripcion: 'Existen productos sin sector asignado',
                cantidad: sinSector.length
            });
        }

        // Productos sin línea estratégica
        const sinLinea = pdmData.planIndicativoProductos.filter(p => !p.lineaEstrategica || p.lineaEstrategica.trim() === '');
        if (sinLinea.length > 0) {
            inconsistencias.push({
                tipo: 'Productos sin línea estratégica',
                descripcion: 'Existen productos sin línea estratégica asignada',
                cantidad: sinLinea.length
            });
        }

        // Productos sin programación
        const sinProgramacion = pdmData.planIndicativoProductos.filter(p =>
            p.programacion2024 === 0 &&
            p.programacion2025 === 0 &&
            p.programacion2026 === 0 &&
            p.programacion2027 === 0
        );
        if (sinProgramacion.length > 0) {
            inconsistencias.push({
                tipo: 'Productos sin programación',
                descripcion: 'Existen productos sin programación para ningún año del cuatrienio',
                cantidad: sinProgramacion.length
            });
        }

        // Productos con programación pero sin presupuesto
        const sinPresupuesto = pdmData.planIndicativoProductos.filter(p =>
            (p.programacion2024 > 0 || p.programacion2025 > 0 || p.programacion2026 > 0 || p.programacion2027 > 0) &&
            p.total2024 === 0 && p.total2025 === 0 && p.total2026 === 0 && p.total2027 === 0
        );
        if (sinPresupuesto.length > 0) {
            inconsistencias.push({
                tipo: 'Productos programados sin presupuesto',
                descripcion: 'Existen productos con programación pero sin presupuesto asignado',
                cantidad: sinPresupuesto.length
            });
        }

        return inconsistencias;
    }

    // Métodos auxiliares
    private encontrarHoja(workbook: XLSX.WorkBook, nombresAlternativos: string[]): string | null {
        for (const nombre of nombresAlternativos) {
            if (workbook.Sheets[nombre]) {
                return nombre;
            }
        }
        // Buscar por coincidencia parcial
        for (const nombreHoja of workbook.SheetNames) {
            for (const nombreAlt of nombresAlternativos) {
                if (nombreHoja.toLowerCase().includes(nombreAlt.toLowerCase())) {
                    return nombreHoja;
                }
            }
        }
        return null;
    }

    private mapearDatos<T>(jsonData: any[], mapper: (row: any[]) => T): T[] {
        // Saltar las primeras filas de encabezado
        const datos = jsonData.slice(2); // Asume que las primeras 2 filas son encabezados
        return datos
            .filter(row => row && row.length > 0 && row[0]) // Filtrar filas vacías
            .map(mapper)
            .filter(item => Object.values(item as any).some(v => v !== '' && v !== null && v !== undefined));
    }

    private limpiarValor(valor: any): string {
        if (valor === null || valor === undefined) return '';
        return String(valor).trim();
    }

    private convertirNumero(valor: any): number {
        if (valor === null || valor === undefined || valor === '') return 0;
        const num = typeof valor === 'number' ? valor : parseFloat(String(valor).replace(/[^0-9.-]/g, ''));
        return isNaN(num) ? 0 : num;
    }

    // Métodos públicos para obtener datos filtrados
    obtenerDatosFiltrados(filtros: FiltrosPDM): PlanIndicativoProducto[] {
        const data = this.pdmDataSubject.value;
        if (!data) return [];

        let productos = [...data.planIndicativoProductos];

        if (filtros.sector) {
            productos = productos.filter(p => p.sector === filtros.sector);
        }

        if (filtros.lineaEstrategica) {
            productos = productos.filter(p => p.lineaEstrategica === filtros.lineaEstrategica);
        }

        if (filtros.estado) {
            productos = productos.filter(p => p.estado === filtros.estado);
        }

        if (filtros.secretaria) {
            productos = productos.filter(p => (p.secretariaAsignada || '') === filtros.secretaria);
        }

        return productos;
    }

    obtenerSectoresUnicos(): string[] {
        const data = this.pdmDataSubject.value;
        if (!data) return [];
        return [...new Set(data.planIndicativoProductos.map(p => p.sector))].filter(s => s).sort();
    }

    obtenerLineasEstrategicasUnicas(): string[] {
        const data = this.pdmDataSubject.value;
        if (!data) return [];
        return [...new Set(data.planIndicativoProductos.map(p => p.lineaEstrategica))].filter(l => l).sort();
    }

    obtenerSecretariasUnicas(): string[] {
        const data = this.pdmDataSubject.value;
        if (!data) return [];
        return [...new Set(data.planIndicativoProductos.map(p => p.secretariaAsignada).filter(Boolean) as string[])]
            .filter(s => s)
            .sort();
    }

    limpiarDatos(): void {
        this.pdmDataSubject.next(null);
        this.analisisSubject.next(null);
        this.limpiarCache();
    }
}
