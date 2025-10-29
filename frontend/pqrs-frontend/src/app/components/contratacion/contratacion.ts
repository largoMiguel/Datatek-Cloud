import { Component, OnDestroy, OnInit, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { BaseChartDirective } from 'ng2-charts';
import { Chart, ChartConfiguration, ChartData, ChartType, registerables } from 'chart.js';
import { ContratacionService } from '../../services/contratacion.service';
import { ProcesoContratacion, FiltroContratacion, KPIsContratacion } from '../../models/contratacion.model';
import { EntityContextService } from '../../services/entity-context.service';
import { AuthService } from '../../services/auth.service';
import { Subscription, filter, combineLatest } from 'rxjs';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
import { AiReportService, ContratacionSummaryPayload } from '../../services/ai-report.service';

Chart.register(...registerables);

@Component({
    selector: 'app-contratacion',
    standalone: true,
    imports: [CommonModule, FormsModule, BaseChartDirective, RouterModule],
    templateUrl: './contratacion.html',
    styleUrls: ['./contratacion.scss']
})
export class ContratacionComponent implements OnInit, OnDestroy {
    @ViewChild(BaseChartDirective) chart?: BaseChartDirective;

    procesos: ProcesoContratacion[] = [];
    procesosFiltrados: ProcesoContratacion[] = [];
    loading = false;
    errorMsg = '';
    subs = new Subscription();
    currentUser: any = null;

    // Vista detallada de KPI
    kpiDetailVisible = false;
    selectedKpi: string = '';

    // Contratos vencidos
    contratosVencidos: ProcesoContratacion[] = [];
    mostrarContratosVencidos = false;

    // Filtros UI
    filtro: FiltroContratacion = {
        entidad: '',
        fechaDesde: new Date(new Date().getFullYear(), 0, 1).toISOString().split('T')[0],
        fechaHasta: new Date().toISOString().split('T')[0],
        modalidad: '',
        tipoContrato: '',
        estado: '',
        adjudicado: '',
        texto: '',
        precioMin: null,
        precioMax: null
    };

    // Catálogos deducidos de los datos
    modalidades: string[] = [];
    tiposContrato: string[] = [];
    estadosResumen: string[] = [];

    // Filtros por columna (tabla)
    columnFilters: {
        referencia?: string;
        estado?: string;
        modalidad?: string;
        tipo?: string;
        precioMin?: number | null;
        precioMax?: number | null;
        proveedor?: string;
        publicacionDesde?: string; // YYYY-MM-DD
        publicacionHasta?: string; // YYYY-MM-DD
        ultimaDesde?: string; // YYYY-MM-DD
        ultimaHasta?: string; // YYYY-MM-DD
    } = {
            referencia: '',
            estado: '',
            modalidad: '',
            tipo: '',
            precioMin: null,
            precioMax: null,
            proveedor: '',
            publicacionDesde: '',
            publicacionHasta: '',
            ultimaDesde: '',
            ultimaHasta: ''
        };

    // KPIs
    kpis: KPIsContratacion = {
        totalProcesos: 0,
        totalAdjudicados: 0,
        tasaAdjudicacion: 0,
        sumaAdjudicado: 0,
        promedioPrecioBase: 0
    };

    // Charts
    doughnutChartType: ChartType = 'doughnut';
    barChartType: ChartType = 'bar';
    lineChartType: ChartType = 'line';

    chartOptions: ChartConfiguration['options'] = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: true, position: 'bottom' } }
    };

    estadosChartData: ChartData<'doughnut'> = { labels: [], datasets: [] };
    modalidadesChartData: ChartData<'bar'> = { labels: [], datasets: [] };
    timelineChartData: ChartData<'line'> = { labels: [], datasets: [] };
    proveedoresChartData: ChartData<'bar'> = { labels: [], datasets: [] };
    tiposContratoChartData: ChartData<'doughnut'> = { labels: [], datasets: [] };
    proveedoresChartOptions: ChartConfiguration['options'] = {
        responsive: true,
        maintainAspectRatio: false,
        indexAxis: 'y',
        plugins: { legend: { display: false } }
    };

    generatingPdf = false;

    constructor(
        private contratacionService: ContratacionService,
        public entityContext: EntityContextService,
        private authService: AuthService,
        private aiReport: AiReportService,
        private router: Router
    ) {
        this.currentUser = this.authService.getCurrentUserValue();
    }

    ngOnInit(): void {
        // Relanzar carga cuando cambia la entidad
        const sub = this.entityContext.currentEntity$.pipe(
            filter(e => !!e)
        ).subscribe(entity => {
            // Usar el NIT de la entidad para consultas SECOP
            const nit = entity!.nit || '891801994'; // NIT de ejemplo si no tiene
            this.filtro.entidad = nit;

            console.log(`[Contratación] NIT de la entidad: ${nit}`);
            this.fetch();
        });
        this.subs.add(sub);
    } ngOnDestroy(): void {
        this.subs.unsubscribe();
    }

    fetch(): void {
        this.loading = true;
        this.errorMsg = '';
        this.contratacionService.fetchProcesos(this.filtro).subscribe({
            next: (rows) => {
                this.procesos = rows;
                if (rows.length === 0) {
                    this.errorMsg = `No se encontraron datos de contratación para el NIT "${this.filtro.entidad}" en el rango de fechas seleccionado. Verifica que el NIT de la entidad esté configurado correctamente en el super admin.`;
                }
                this.applyLocalFilters();
                this.loading = false;
            },
            error: (err) => {
                console.error('[Contratación] Error al cargar datos:', err);
                this.errorMsg = 'No se pudo cargar la información de contratación. Verifica la conexión con el servidor.';
                this.loading = false;
            }
        });
    }

    // Filtrado adicional en cliente (búsqueda y rangos ya cubiertos, mantenemos por si llega sin tipado numérico)
    applyLocalFilters(): void {
        let data = [...this.procesos];

        // Actualizar catálogos
        this.modalidades = Array.from(new Set(data.map(d => d.modalidad_de_contratacion).filter(Boolean))) as string[];
        this.tiposContrato = Array.from(new Set(data.map(d => d.tipo_de_contrato).filter(Boolean))) as string[];
        this.estadosResumen = Array.from(new Set(data.map(d => d.estado_resumen).filter(Boolean))) as string[];

        // Filtros por columna
        const cf = this.columnFilters;
        if (cf.referencia) {
            const needle = cf.referencia.toLowerCase();
            data = data.filter(p => (p.referencia_del_proceso || '').toLowerCase().includes(needle));
        }
        if (cf.estado) {
            data = data.filter(p => (p.estado_resumen || '') === cf.estado);
        }
        if (cf.modalidad) {
            data = data.filter(p => (p.modalidad_de_contratacion || '') === cf.modalidad);
        }
        if (cf.tipo) {
            data = data.filter(p => (p.tipo_de_contrato || '') === cf.tipo);
        }
        if (cf.precioMin != null && cf.precioMin !== undefined) {
            data = data.filter(p => this.toNumber(p.precio_base) >= (cf.precioMin || 0));
        }
        if (cf.precioMax != null && cf.precioMax !== undefined) {
            data = data.filter(p => this.toNumber(p.precio_base) <= (cf.precioMax || Number.MAX_SAFE_INTEGER));
        }
        if (cf.proveedor) {
            const needle = cf.proveedor.toLowerCase();
            data = data.filter(p => (p.nombre_del_proveedor || '').toString().toLowerCase().includes(needle));
        }
        if (cf.publicacionDesde) {
            const d = new Date(cf.publicacionDesde);
            data = data.filter(p => !p.fecha_de_publicacion_del || new Date(p.fecha_de_publicacion_del) >= d);
        }
        if (cf.publicacionHasta) {
            const d = new Date(cf.publicacionHasta);
            data = data.filter(p => !p.fecha_de_publicacion_del || new Date(p.fecha_de_publicacion_del) <= d);
        }
        if (cf.ultimaDesde) {
            const d = new Date(cf.ultimaDesde);
            data = data.filter(p => !p.fecha_de_ultima_publicaci || new Date(p.fecha_de_ultima_publicaci) >= d);
        }
        if (cf.ultimaHasta) {
            const d = new Date(cf.ultimaHasta);
            data = data.filter(p => !p.fecha_de_ultima_publicaci || new Date(p.fecha_de_ultima_publicaci) <= d);
        }

        // Orden por referencia
        data.sort((a, b) => (a.referencia_del_proceso || '').localeCompare(b.referencia_del_proceso || ''));

        this.procesosFiltrados = data;
        this.computeKPIs();
        this.updateCharts();
        this.detectarContratosVencidos();
    }

    detectarContratosVencidos(): void {
        const hoy = new Date();
        this.contratosVencidos = this.procesosFiltrados.filter(p => {
            // Solo contratos adjudicados (lógica normalizada)
            if (!this.isAdjudicado(p)) return false;

            // Verificar si tiene fecha de adjudicación y duración
            if (!p.fecha_adjudicacion || !p.duracion) return false;

            const fechaAdjudicacion = new Date(p.fecha_adjudicacion);
            const duracionNum = typeof p.duracion === 'number' ? p.duracion : parseInt(String(p.duracion));
            const unidad = p.unidad_de_duracion || 'Dias';

            if (isNaN(duracionNum) || duracionNum <= 0) return false;

            // Convertir duración a días
            let duracionDias = duracionNum;
            const unidadLower = unidad.toLowerCase();
            if (unidadLower.includes('mes')) {
                duracionDias = duracionNum * 30;
            } else if (unidadLower.includes('año') || unidadLower.includes('ano')) {
                duracionDias = duracionNum * 365;
            }

            // Calcular fecha de finalización
            const fechaFin = new Date(fechaAdjudicacion);
            fechaFin.setDate(fechaFin.getDate() + duracionDias);

            // El contrato está vencido si la fecha de fin es anterior a hoy
            return fechaFin < hoy;
        });

        console.log(`[Contratación] Contratos vencidos detectados: ${this.contratosVencidos.length}`);
    }

    calcularDiasVencidos(contrato: ProcesoContratacion): number {
        if (!contrato.fecha_adjudicacion || !contrato.duracion) return 0;

        const fechaAdjudicacion = new Date(contrato.fecha_adjudicacion);
        const duracionNum = typeof contrato.duracion === 'number' ? contrato.duracion : parseInt(String(contrato.duracion));
        const unidad = contrato.unidad_de_duracion || 'Dias';

        if (isNaN(duracionNum)) return 0;

        // Convertir duración a días
        let duracionDias = duracionNum;
        const unidadLower = unidad.toLowerCase();
        if (unidadLower.includes('mes')) {
            duracionDias = duracionNum * 30;
        } else if (unidadLower.includes('año') || unidadLower.includes('ano')) {
            duracionDias = duracionNum * 365;
        }

        const fechaFin = new Date(fechaAdjudicacion);
        fechaFin.setDate(fechaFin.getDate() + duracionDias);

        const hoy = new Date();
        const diffTime = hoy.getTime() - fechaFin.getTime();
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

        return diffDays > 0 ? diffDays : 0;
    }

    formatearDuracion(contrato: ProcesoContratacion): string {
        if (!contrato.duracion) return 'N/D';
        const duracion = contrato.duracion;
        const unidad = contrato.unidad_de_duracion || 'Días';
        return `${duracion} ${unidad}`;
    }

    computeKPIs(): void {
        const total = this.procesosFiltrados.length;
        const adjudicados = this.procesosFiltrados.filter(p => this.isAdjudicado(p));
        const sumaAdj = adjudicados.reduce((acc, p) => acc + this.toNumber(p.valor_total_adjudicacion), 0);
        const promedioPrecio = this.avg(this.procesosFiltrados.map(p => this.toNumber(p.precio_base)));

        this.kpis = {
            totalProcesos: total,
            totalAdjudicados: adjudicados.length,
            tasaAdjudicacion: total ? adjudicados.length / total : 0,
            sumaAdjudicado: sumaAdj,
            promedioPrecioBase: promedioPrecio
        };
    }

    updateCharts(): void {
        // Estados
        const estados = this.groupCount(this.procesosFiltrados.map(p => p.estado_resumen || 'SIN ESTADO'));
        this.estadosChartData = {
            labels: Object.keys(estados),
            datasets: [{
                data: Object.values(estados),
                backgroundColor: ['#216ba8', '#28a745', '#ffc107', '#dc3545', '#6c757d', '#17a2b8', '#6610f2', '#20c997']
            }]
        };

        // Modalidades
        const mods = this.groupCount(this.procesosFiltrados.map(p => p.modalidad_de_contratacion || 'N/D'));
        this.modalidadesChartData = {
            labels: Object.keys(mods),
            datasets: [{
                label: 'Procesos',
                data: Object.values(mods),
                backgroundColor: 'rgba(33, 107, 168, 0.7)',
                borderColor: 'rgba(33, 107, 168, 1)',
                borderWidth: 2
            }]
        };

        // Timeline por mes (conteo por publicación)
        const byMonth = this.groupCount(this.procesosFiltrados.map(p => this.toMonth(p.fecha_de_publicacion_del)));
        const labels = Object.keys(byMonth).sort();
        this.timelineChartData = {
            labels,
            datasets: [{
                label: 'Publicaciones',
                data: labels.map(l => byMonth[l] || 0),
                borderColor: '#216ba8',
                backgroundColor: 'rgba(33, 107, 168, 0.1)',
                fill: true,
                tension: 0.3
            }]
        };

        // Top proveedores por valor adjudicado
        this.computeTopProveedoresChart();

        // Tipos de contrato
        this.computeTiposContratoChart();

        if (this.chart) this.chart.update();
    }

    private computeTiposContratoChart(): void {
        const map = new Map<string, number>();
        for (const p of this.procesosFiltrados) {
            const tipo = p.tipo_de_contrato || 'Sin especificar';
            map.set(tipo, (map.get(tipo) || 0) + 1);
        }
        const pairs = Array.from(map.entries()).sort((a, b) => b[1] - a[1]);
        const labels = pairs.map(([tipo]) => tipo);
        const data = pairs.map(([, count]) => count);

        const colors = [
            'rgba(33, 107, 168, 0.7)',
            'rgba(40, 167, 69, 0.7)',
            'rgba(255, 193, 7, 0.7)',
            'rgba(23, 162, 184, 0.7)',
            'rgba(220, 53, 69, 0.7)',
            'rgba(108, 117, 125, 0.7)'
        ];

        this.tiposContratoChartData = {
            labels,
            datasets: [{
                label: 'Cantidad',
                data,
                backgroundColor: colors,
                borderColor: colors.map(c => c.replace('0.7', '1')),
                borderWidth: 2
            }]
        };
    }

    // Helpers
    toNumber(v: any): number {
        if (v === null || v === undefined) return 0;
        if (typeof v === 'number') return v;
        const s = String(v).replace(/[^0-9.-]/g, '');
        const n = Number(s);
        return isNaN(n) ? 0 : n;
    }

    // URL helper para enlaces externos del proceso (SECOP II)
    getProcesoUrl(p: ProcesoContratacion): string {
        const resolve = (u: any): string => {
            if (!u) return '#';
            if (typeof u === 'string') return u;
            if (typeof u === 'object') {
                if ('url' in u && u.url) return String(u.url);
                if ('href' in u && u.href) return String(u.href);
                if ('value' in u && u.value) return String(u.value);
                if (Array.isArray(u)) return resolve(u[0]);
            }
            return '#';
        };

        const raw = (p as any)?.urlproceso;
        const url = resolve(raw);
        // Validación ligera del esquema
        try {
            const parsed = new URL(url, window?.location?.origin || undefined);
            return parsed.toString();
        } catch {
            return url || '#';
        }
    }

    avg(nums: number[]): number {
        const list = nums.filter(n => typeof n === 'number' && !isNaN(n));
        if (!list.length) return 0;
        return Math.round((list.reduce((a, b) => a + b, 0) / list.length) * 100) / 100;
    }

    // Normaliza si un proceso está adjudicado
    isAdjudicado(p: ProcesoContratacion): boolean {
        const estado = (p.estado_resumen ?? '').toString().trim().toUpperCase();
        const adj = p.adjudicado;
        if (typeof adj === 'boolean') {
            if (adj) return true;
        } else {
            const s = (adj ?? '').toString().trim().toUpperCase();
            if (s === 'SI' || s === 'TRUE' || s === '1') return true;
        }
        if (estado.includes('ADJUDICADO')) return true;
        if (p.fecha_adjudicacion) return true;
        return false;
    }

    // Clase visual para estado
    getEstadoBadgeClass(p: ProcesoContratacion): string {
        const e = (p.estado_resumen ?? '').toString().trim().toUpperCase();
        if (e.includes('ADJUDICADO') || e.includes('CELEBRADO')) return 'bg-success';
        if (e.includes('PUBLICADO') || e.includes('EN PUBLICACIÓN')) return 'bg-primary';
        if (e.includes('CANCELADO') || e.includes('SUSPENDIDO')) return 'bg-danger';
        if (e.includes('DESIERTO')) return 'bg-warning';
        return 'bg-secondary';
    }

    groupCount(arr: string[]): Record<string, number> {
        return arr.reduce((acc: Record<string, number>, key) => {
            acc[key] = (acc[key] || 0) + 1;
            return acc;
        }, {});
    }

    toMonth(iso?: string): string {
        if (!iso) return 'N/D';
        const d = new Date(iso);
        if (isNaN(d.getTime())) return 'N/D';
        return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
    }

    // Acciones UI
    buscar(): void {
        this.fetch();
    }

    limpiar(): void {
        this.filtro = {
            entidad: this.filtro.entidad,
            fechaDesde: new Date(new Date().getFullYear(), 0, 1).toISOString().split('T')[0],
            fechaHasta: new Date().toISOString().split('T')[0],
            modalidad: '',
            tipoContrato: '',
            estado: '',
            adjudicado: '',
            texto: '',
            precioMin: null,
            precioMax: null
        };
        // Limpiar filtros de columna locales
        this.columnFilters = {
            referencia: '', estado: '', modalidad: '', tipo: '',
            precioMin: null, precioMax: null, proveedor: '',
            publicacionDesde: '', publicacionHasta: '', ultimaDesde: '', ultimaHasta: ''
        };
        this.fetch();
    }

    exportCSV(): void {
        const headers = [
            'referencia_del_proceso', 'fase', 'fecha_de_publicacion_del', 'fecha_de_ultima_publicaci', 'precio_base',
            'modalidad_de_contratacion', 'duracion', 'unidad_de_duracion', 'fecha_de_recepcion_de', 'fecha_de_apertura_efectiva',
            'adjudicado', 'fecha_adjudicacion', 'valor_total_adjudicacion', 'nombre_del_proveedor', 'estado_de_apertura_del_proceso',
            'estado_resumen', 'urlproceso', 'descripci_n_del_procedimiento', 'tipo_de_contrato'
        ];
        const rows = this.procesosFiltrados.map(p => headers.map(h => (p as any)[h] ?? ''));
        const csv = [headers.join(','), ...rows.map(r => r.map(v => `"${String(v).replace(/"/g, '""')}"`).join(','))].join('\n');
        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `contratacion_${this.filtro.entidad || 'entidad'}_${this.filtro.fechaDesde}_${this.filtro.fechaHasta}.csv`;
        a.click();
        URL.revokeObjectURL(url);
    }

    private computeTopProveedoresChart(): void {
        const map = new Map<string, number>();
        for (const p of this.procesosFiltrados) {
            const prov = (p.nombre_del_proveedor || 'N/D').toString();
            const val = this.toNumber(p.valor_total_adjudicacion);
            if (val > 0) map.set(prov, (map.get(prov) || 0) + val);
        }
        const pairs = Array.from(map.entries()).sort((a, b) => b[1] - a[1]).slice(0, 10);
        const labels = pairs.map(([prov]) => prov);
        const data = pairs.map(([, valor]) => valor);
        this.proveedoresChartData = {
            labels,
            datasets: [{
                label: 'Total adjudicado',
                data,
                backgroundColor: 'rgba(40, 167, 69, 0.7)',
                borderColor: 'rgba(40, 167, 69, 1)',
                borderWidth: 2
            }]
        };
    }

    // Métodos de navegación
    logout(): void {
        this.authService.logout();
        this.router.navigate([`/${this.entityContext.currentEntity?.slug}/login`]);
    }

    pqrsEnabled(): boolean {
        return this.entityContext.currentEntity?.enable_pqrs ?? false;
    }

    planesEnabled(): boolean {
        return this.entityContext.currentEntity?.enable_planes_institucionales ?? false;
    }

    contratacionEnabled(): boolean {
        return this.entityContext.currentEntity?.enable_contratacion ?? false;
    }

    usersAdminEnabled(): boolean {
        return this.entityContext.currentEntity?.enable_users_admin ?? false;
    }

    isAdmin(): boolean {
        return this.currentUser?.role === 'admin';
    }

    // Métodos para KPIs clickeables
    toggleKpiDetail(kpiType: string): void {
        if (this.selectedKpi === kpiType) {
            this.kpiDetailVisible = !this.kpiDetailVisible;
        } else {
            this.selectedKpi = kpiType;
            this.kpiDetailVisible = true;
        }
    }

    getKpiDetail(): any {
        switch (this.selectedKpi) {
            case 'procesos':
                return {
                    title: 'Detalle de Procesos',
                    items: [
                        { label: 'Total registros', value: this.procesos.length },
                        { label: 'Procesos filtrados', value: this.procesosFiltrados.length },
                        { label: 'Promedio precio base', value: `$ ${this.kpis.promedioPrecioBase.toLocaleString()}` }
                    ]
                };
            case 'adjudicados':
                const noAdjudicados = this.kpis.totalProcesos - this.kpis.totalAdjudicados;
                return {
                    title: 'Detalle de Adjudicación',
                    items: [
                        { label: 'Procesos adjudicados', value: this.kpis.totalAdjudicados },
                        { label: 'Procesos sin adjudicar', value: noAdjudicados },
                        { label: 'Tasa de éxito', value: `${(this.kpis.tasaAdjudicacion * 100).toFixed(1)}%` }
                    ]
                };
            case 'tasa':
                return {
                    title: 'Análisis de Tasa',
                    items: [
                        { label: 'Procesos evaluados', value: this.kpis.totalProcesos },
                        { label: 'Exitosos', value: this.kpis.totalAdjudicados },
                        { label: 'Porcentaje', value: `${(this.kpis.tasaAdjudicacion * 100).toFixed(2)}%` }
                    ]
                };
            case 'monto':
                return {
                    title: 'Análisis de Montos',
                    items: [
                        { label: 'Total adjudicado', value: `$ ${this.kpis.sumaAdjudicado.toLocaleString()}` },
                        { label: 'Promedio por contrato', value: `$ ${(this.kpis.sumaAdjudicado / Math.max(this.kpis.totalAdjudicados, 1)).toLocaleString('es-CO', { maximumFractionDigits: 0 })}` },
                        { label: 'Contratos adjudicados', value: this.kpis.totalAdjudicados }
                    ]
                };
            default:
                return null;
        }
    }

    // Métodos para filtros de columna
    onColumnFilterChange(): void {
        this.applyLocalFilters();
    }

    clearColumnFilters(): void {
        this.columnFilters = {
            referencia: '', estado: '', modalidad: '', tipo: '',
            precioMin: null, precioMax: null, proveedor: '',
            publicacionDesde: '', publicacionHasta: '', ultimaDesde: '', ultimaHasta: ''
        };
        this.applyLocalFilters();
    }

    // ===== Reporte PDF =====
    private getChartImage(chartId: string): string | null {
        const canvas = document.getElementById(chartId) as HTMLCanvasElement | null;
        if (!canvas) return null;
        try {
            return canvas.toDataURL('image/png', 1.0);
        } catch {
            return null;
        }
    }

    private buildSummaryPayload(): ContratacionSummaryPayload {
        // Distribuciones a partir de chart data
        const distribEstados: Record<string, number> = {};
        (this.estadosChartData.labels || []).forEach((l: any, i: number) => {
            const v = (this.estadosChartData.datasets[0] as any)?.data?.[i] ?? 0;
            distribEstados[String(l)] = Number(v);
        });
        const distribModalidades: Record<string, number> = {};
        (this.modalidadesChartData.labels || []).forEach((l: any, i: number) => {
            const v = (this.modalidadesChartData.datasets[0] as any)?.data?.[i] ?? 0;
            distribModalidades[String(l)] = Number(v);
        });
        const distribTipos: Record<string, number> = {};
        (this.tiposContratoChartData.labels || []).forEach((l: any, i: number) => {
            const v = (this.tiposContratoChartData.datasets[0] as any)?.data?.[i] ?? 0;
            distribTipos[String(l)] = Number(v);
        });

        const top_proveedores: Array<{ nombre: string; valor: number }> = [];
        const labels = (this.proveedoresChartData.labels || []) as string[];
        const data = ((this.proveedoresChartData.datasets?.[0] as any)?.data || []) as number[];
        labels.forEach((name, i) => top_proveedores.push({ nombre: name, valor: Number(data[i] || 0) }));

        return {
            entity_name: this.entityContext.currentEntity?.name || null,
            nit: this.entityContext.currentEntity?.nit || this.filtro.entidad || null,
            periodo: { desde: this.filtro.fechaDesde || null, hasta: this.filtro.fechaHasta || null },
            kpis: {
                totalProcesos: this.kpis.totalProcesos,
                totalAdjudicados: this.kpis.totalAdjudicados,
                tasaAdjudicacion: this.kpis.tasaAdjudicacion,
                sumaAdjudicado: this.kpis.sumaAdjudicado,
                promedioPrecioBase: this.kpis.promedioPrecioBase
            },
            distribuciones: {
                estados: distribEstados,
                modalidades: distribModalidades,
                tiposContrato: distribTipos
            },
            top_proveedores
        };
    }

    generatePdfWithAI(): void {
        if (!this.procesosFiltrados.length) return;
        this.generatingPdf = true;
        const payload = this.buildSummaryPayload();
        this.aiReport.summarizeContratacion(payload).subscribe({
            next: (res) => {
                this.generatePdf(res.summary || undefined);
                this.generatingPdf = false;
            },
            error: () => {
                // Si falla IA, generamos PDF sin IA
                this.generatePdf();
                this.generatingPdf = false;
            }
        });
    }

    generatePdf(aiSummary?: string): void {
        const doc = new jsPDF({ unit: 'pt', format: 'a4' });
        const margin = 40;
        let y = margin;

        const entityName = this.entityContext.currentEntity?.name || 'Entidad';
        const nit = this.entityContext.currentEntity?.nit || this.filtro.entidad || 'N/D';

        // Encabezado
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(16);
        doc.text(`Informe de Contratación Pública - SECOP II`, margin, y); y += 22;
        doc.setFont('helvetica', 'normal');
        doc.setFontSize(11);
        doc.text(`Entidad: ${entityName}  |  NIT: ${nit}`, margin, y); y += 16;
        doc.text(`Periodo: ${this.filtro.fechaDesde} a ${this.filtro.fechaHasta}`, margin, y); y += 10;
        doc.text(`Generado: ${new Date().toLocaleString('es-CO')}`, margin, y); y += 18;

        // Línea
        doc.setDrawColor(33, 107, 168);
        doc.line(margin, y, 555, y); y += 14;

        // KPIs
        doc.setFont('helvetica', 'bold');
        doc.text('Resumen de Indicadores', margin, y); y += 14;
        doc.setFont('helvetica', 'normal');
        const k = this.kpis;
        const kpiLines = [
            `Total procesos: ${k.totalProcesos}`,
            `Adjudicados: ${k.totalAdjudicados} (${(k.tasaAdjudicacion * 100).toFixed(1)}%)`,
            `Total adjudicado: $ ${Math.round(k.sumaAdjudicado).toLocaleString('es-CO')}`,
            `Precio base promedio: $ ${Math.round(k.promedioPrecioBase).toLocaleString('es-CO')}`
        ];
        kpiLines.forEach(line => { doc.text(line, margin, y); y += 14; });
        y += 6;

        // Resumen IA (opcional)
        if (aiSummary) {
            doc.setFont('helvetica', 'bold');
            doc.text('Resumen con IA', margin, y); y += 14;
            doc.setFont('helvetica', 'normal');
            const split = doc.splitTextToSize(aiSummary, 515);
            split.forEach((line: string) => {
                if (y > 770) { doc.addPage(); y = margin; }
                doc.text(line, margin, y);
                y += 14;
            });
            y += 6;
        }

        // Gráficas como imágenes
        const charts = [
            { id: 'chart-estados', title: 'Distribución por Estado' },
            { id: 'chart-modalidades', title: 'Modalidades' },
            { id: 'chart-tipos', title: 'Tipos de Contrato' },
            { id: 'chart-proveedores', title: 'Top Proveedores por Valor' },
            { id: 'chart-timeline', title: 'Timeline de Publicaciones' }
        ];
        for (const c of charts) {
            const img = this.getChartImage(c.id);
            if (!img) continue;
            if (y > 700) { doc.addPage(); y = margin; }
            doc.setFont('helvetica', 'bold');
            doc.text(c.title, margin, y); y += 10;
            try {
                doc.addImage(img, 'PNG', margin, y, 515, 220, undefined, 'FAST');
                y += 230;
            } catch { /* ignore image errors */ }
        }

        // Tabla (resumen top 20 por tamaño)
        const headers = [
            'Referencia', 'Estado', 'Modalidad', 'Tipo', 'Precio base', 'Proveedor', 'Publicación', 'Últ. pub.'
        ];
        const body = this.procesosFiltrados.slice(0, 20).map(p => [
            p.referencia_del_proceso || '-',
            p.estado_resumen || '-',
            p.modalidad_de_contratacion || '-',
            p.tipo_de_contrato || '-',
            `$ ${this.toNumber(p.precio_base).toLocaleString('es-CO')}`,
            p.nombre_del_proveedor || '-',
            p.fecha_de_publicacion_del ? new Date(p.fecha_de_publicacion_del).toLocaleDateString('es-CO') : '-',
            p.fecha_de_ultima_publicaci ? new Date(p.fecha_de_ultima_publicaci).toLocaleDateString('es-CO') : '-',
        ]);

        autoTable(doc, {
            head: [headers],
            body,
            startY: y,
            styles: { fontSize: 8 },
            headStyles: { fillColor: [33, 107, 168] },
            theme: 'grid',
            margin: { left: margin, right: margin }
        });

        // Guardar
        const file = `informe_contratacion_${(this.entityContext.currentEntity?.slug || 'entidad')}_${this.filtro.fechaDesde}_${this.filtro.fechaHasta}.pdf`;
        doc.save(file);
    }
}
