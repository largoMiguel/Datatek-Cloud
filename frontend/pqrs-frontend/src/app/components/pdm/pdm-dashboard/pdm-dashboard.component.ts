import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { Subject, takeUntil, forkJoin, of } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { ChartConfiguration, ChartData } from 'chart.js';
import { BaseChartDirective } from 'ng2-charts';
import { PdmDataService } from '../pdm-data.service';
import { AnalisisPDM, PDMData, FiltrosPDM, EstadoMeta, PlanIndicativoProducto } from '../pdm.models';
import { PdmBackendService } from '../../../services/pdm-backend.service';
import { EntityContextService } from '../../../services/entity-context.service';
import { PdmAvanceDialogComponent, AvanceDialogData } from '../pdm-avance-dialog/pdm-avance-dialog.component';

declare const bootstrap: any;

@Component({
    selector: 'app-pdm-dashboard',
    standalone: true,
    imports: [
        CommonModule,
        FormsModule,
        BaseChartDirective,
        PdmAvanceDialogComponent
    ],
    templateUrl: './pdm-dashboard.component.html',
    styleUrls: ['./pdm-dashboard.component.scss']
})
export class PdmDashboardComponent implements OnInit, OnDestroy {

    private destroy$ = new Subject<void>();

    pdmData: PDMData | null = null;
    analisis: AnalisisPDM | null = null;
    cargando = false;

    // Filtros
    filtros: FiltrosPDM = {};
    sectoresDisponibles: string[] = [];
    lineasDisponibles: string[] = [];
    secretariasDisponibles: string[] = [];
    estadosDisponibles = [
        { valor: EstadoMeta.CUMPLIDA, etiqueta: 'Cumplida' },
        { valor: EstadoMeta.EN_PROGRESO, etiqueta: 'En Progreso' },
        { valor: EstadoMeta.POR_CUMPLIR, etiqueta: 'Por Cumplir' },
        { valor: EstadoMeta.PENDIENTE, etiqueta: 'Pendiente' },
        { valor: EstadoMeta.SIN_DEFINIR, etiqueta: 'Sin Definir' }
    ];

    // Tabla
    displayedColumns: string[] = ['codigo', 'sector', 'producto', 'secretaria', 'meta', 'a2024', 'a2025', 'a2026', 'a2027', 'avance', 'estado', 'presupuesto', 'acciones'];
    productos: PlanIndicativoProducto[] = [];
    productosFiltrados: PlanIndicativoProducto[] = [];
    searchTerm: string = '';
    currentPage = 1;
    itemsPerPage = 10;
    sortColumn: string = '';
    sortDirection: 'asc' | 'desc' = 'asc';

    // Gráficos
    chartPorAnio: ChartData<'bar'> | null = null;
    chartPorSector: ChartData<'bar'> | null = null;
    chartCumplimiento: ChartData<'doughnut'> | null = null;
    chartPresupuesto: ChartData<'line'> | null = null;
    chartODS: ChartData<'doughnut'> | null = null;
    chartODSPresupuesto: ChartData<'bar'> | null = null;
    chartSGRPorSector: ChartData<'bar'> | null = null;
    chartIndicadoresPND: ChartData<'doughnut'> | null = null;
    chartIndicadoresPorLinea: ChartData<'bar'> | null = null;
    chartPresupuestoOrdinarioVsSGR: ChartData<'doughnut'> | null = null;
    chartPresupuestoPorAnioDetallado: ChartData<'bar'> | null = null;
    chartPresupuestoPorSectorDetallado: ChartData<'bar'> | null = null;

    chartOptions: ChartConfiguration<'bar'>['options'] = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: true,
                position: 'top',
                labels: {
                    font: {
                        size: 12,
                        family: "'Inter', sans-serif"
                    },
                    padding: 16,
                    usePointStyle: true
                }
            },
            tooltip: {
                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                padding: 12,
                cornerRadius: 8,
                titleFont: {
                    size: 13,
                    weight: 'bold'
                },
                bodyFont: {
                    size: 12
                }
            }
        },
        scales: {
            x: {
                grid: {
                    display: false
                }
            },
            y: {
                grid: {
                    color: 'rgba(0, 0, 0, 0.05)'
                },
                ticks: {
                    precision: 0
                }
            }
        }
    };

    barHorizontalOptions: ChartConfiguration<'bar'>['options'] = {
        responsive: true,
        maintainAspectRatio: false,
        indexAxis: 'y',
        plugins: {
            legend: {
                display: false
            },
            tooltip: {
                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                padding: 12,
                cornerRadius: 8
            }
        },
        scales: {
            x: {
                grid: {
                    color: 'rgba(0, 0, 0, 0.05)'
                },
                ticks: {
                    callback: function (value) {
                        return value + '%';
                    }
                }
            },
            y: {
                grid: {
                    display: false
                }
            }
        }
    };

    doughnutOptions: ChartConfiguration<'doughnut'>['options'] = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: true,
                position: 'right',
                labels: {
                    font: {
                        size: 12,
                        family: "'Inter', sans-serif"
                    },
                    padding: 12,
                    usePointStyle: true,
                    generateLabels: (chart) => {
                        const data = chart.data;
                        if (data.labels && data.datasets.length) {
                            return data.labels.map((label, i) => {
                                const value = data.datasets[0].data[i] as number;
                                return {
                                    text: `${label}: ${value}`,
                                    fillStyle: (data.datasets[0].backgroundColor as string[])[i],
                                    hidden: false,
                                    index: i
                                };
                            });
                        }
                        return [];
                    }
                }
            },
            tooltip: {
                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                padding: 12,
                cornerRadius: 8,
                callbacks: {
                    label: function (context) {
                        const label = context.label || '';
                        const value = context.parsed || 0;
                        const total = (context.dataset.data as number[]).reduce((a, b) => a + b, 0);
                        const percentage = ((value / total) * 100).toFixed(1);
                        return `${label}: ${value} (${percentage}%)`;
                    }
                }
            }
        }
    };

    lineOptions: ChartConfiguration<'line'>['options'] = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: true,
                position: 'top',
                labels: {
                    font: {
                        size: 12
                    },
                    padding: 16,
                    usePointStyle: true
                }
            },
            tooltip: {
                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                padding: 12,
                cornerRadius: 8
            }
        },
        scales: {
            x: {
                grid: {
                    display: false
                }
            },
            y: {
                grid: {
                    color: 'rgba(0, 0, 0, 0.05)'
                },
                ticks: {
                    callback: function (value) {
                        return new Intl.NumberFormat('es-CO', {
                            style: 'currency',
                            currency: 'COP',
                            notation: 'compact',
                            maximumFractionDigits: 1
                        }).format(value as number);
                    }
                }
            }
        }
    };

    constructor(
        public pdmService: PdmDataService,
        private router: Router,
        private pdmBackend: PdmBackendService,
        private entityContext: EntityContextService
    ) { }

    private showToast(message: string, type: 'success' | 'error' | 'info' = 'info') {
        const toastContainer = document.getElementById('toast-container');
        if (!toastContainer) return;

        const toastId = `toast-${Date.now()}`;
        const bgClass = type === 'success' ? 'bg-success' : type === 'error' ? 'bg-danger' : 'bg-primary';
        const icon = type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle';

        const toastHtml = `
            <div id="${toastId}" class="toast align-items-center text-white ${bgClass} border-0" role="alert">
                <div class="d-flex">
                    <div class="toast-body">
                        <i class="fas ${icon} me-2"></i>${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            </div>
        `;

        toastContainer.insertAdjacentHTML('beforeend', toastHtml);
        const toastElement = document.getElementById(toastId);
        if (toastElement) {
            const toast = new bootstrap.Toast(toastElement, { delay: 3000 });
            toast.show();
            toastElement.addEventListener('hidden.bs.toast', () => toastElement.remove());
        }
    }

    ngOnInit(): void {
        this.pdmService.pdmData$
            .pipe(takeUntil(this.destroy$))
            .subscribe(data => {
                this.pdmData = data;
                if (data) {
                    this.sectoresDisponibles = this.pdmService.obtenerSectoresUnicos();
                    this.lineasDisponibles = this.pdmService.obtenerLineasEstrategicasUnicas();
                    this.secretariasDisponibles = this.pdmService.obtenerSecretariasUnicas();
                    this.actualizarTabla();
                    // Cargar asignaciones guardadas y aplicar a filas
                    const slug = this.entityContext.currentEntity?.slug;
                    if (slug) {
                        this.pdmBackend.getAssignments(slug).subscribe({
                            next: (resp: { assignments: Record<string, string | null> }) => {
                                const map = resp.assignments || {};
                                this.pdmData!.planIndicativoProductos.forEach(p => {
                                    const sec = map[p.codigoIndicadorProducto];
                                    if (sec !== undefined) p.secretariaAsignada = sec || undefined;
                                });
                                this.actualizarTabla();
                                // Luego de asignaciones, cargar avances por cada producto
                                this.cargarAvancesParaTodos(slug);
                            },
                            error: () => { /* silencioso */ }
                        });
                    } else {
                        // Si no hay slug, igual intentamos cargar tabla
                        this.actualizarTabla();
                    }
                } else {
                    // No hay datos, redirigir a la carga
                    this.router.navigate(['pdm-upload'], { relativeTo: this.router.routerState.root });
                }
            });

        this.pdmService.analisis$
            .pipe(takeUntil(this.destroy$))
            .subscribe(analisis => {
                this.analisis = analisis;
                if (analisis) {
                    this.generarGraficos(analisis);
                }
            });

        this.pdmService.cargando$
            .pipe(takeUntil(this.destroy$))
            .subscribe(cargando => {
                this.cargando = cargando;
            });
    }

    onCambiarSecretaria(row: PlanIndicativoProducto, secretaria: string | undefined) {
        const slug = this.entityContext.currentEntity?.slug;
        if (!slug) return;
        this.pdmBackend.upsertAssignment(slug, {
            codigo_indicador_producto: row.codigoIndicadorProducto,
            secretaria: secretaria || null,
        }).subscribe({
            next: () => {
                row.secretariaAsignada = secretaria;
                this.showToast('Secretaría asignada', 'success');
            },
            error: () => this.showToast('No se pudo guardar la asignación', 'error')
        });
    }

    avanceDialogData: AvanceDialogData | null = null;
    avanceModalInstance: any = null;

    // Detalle de producto
    productoSeleccionado: PlanIndicativoProducto | null = null;
    Object = Object; // Para usar Object.keys en el template

    // Gestión de actividades
    actividadesProducto: any[] = [];
    cargandoActividades = false;
    mostrandoFormActividad = false;
    guardandoActividad = false;
    actividadEditando: any = null;
    formActividad: any = {
        nombre: '',
        descripcion: '',
        responsable: '',
        fecha_inicio: '',
        fecha_fin: '',
        porcentaje_avance: 0,
        estado: 'pendiente'
    };

    // Estadísticas avanzadas
    estadisticasPorSecretaria: {
        secretaria: string;
        totalMetas: number;
        avance2024: number;
        avance2025: number;
        avance2026: number;
        avance2027: number;
        avancePromedio: number;
    }[] = [];

    estadisticasPorLinea: {
        lineaEstrategica: string;
        totalMetas: number;
        avance2024: number;
        avance2025: number;
        avance2026: number;
        avance2027: number;
        avancePromedio: number;
    }[] = [];

    abrirDialogoAvance(row: PlanIndicativoProducto | null | undefined) {
        // Validaciones de campos vacíos / nulos
        if (!row || !row.codigoIndicadorProducto) {
            this.showToast('No se puede registrar avance: producto inválido.', 'error');
            return;
        }

        this.avanceDialogData = {
            codigo: row.codigoIndicadorProducto,
            avances: row.avances
        };

        // Esperar a que el DOM se actualice
        setTimeout(() => {
            const modalElement = document.getElementById('avanceModal');
            if (modalElement && bootstrap) {
                this.avanceModalInstance = new bootstrap.Modal(modalElement);
                this.avanceModalInstance.show();
            }
        }, 0);
    }

    onAvanceSave(result: { anio: number; valor_ejecutado: number; comentario: string }) {
        if (!this.avanceDialogData) return;
        const slug = this.entityContext.currentEntity?.slug;
        if (!slug) return;

        const row = this.productos.find(p => p.codigoIndicadorProducto === this.avanceDialogData!.codigo);
        if (!row) return;

        this.pdmBackend.upsertAvance(slug, {
            codigo_indicador_producto: row.codigoIndicadorProducto,
            anio: result.anio,
            valor_ejecutado: result.valor_ejecutado,
            comentario: result.comentario,
        }).subscribe({
            next: () => {
                // Actualizar avances por año en la fila
                if (!row.avances) row.avances = {};
                row.avances[result.anio] = {
                    valor: result.valor_ejecutado,
                    comentario: result.comentario
                };
                // Mantener la métrica general de avance como promedio simple de avances cargados
                const valores = Object.values(row.avances).map(a => a.valor).filter(v => typeof v === 'number');
                row.avance = valores.length ? (valores.reduce((a, b) => a + b, 0) / valores.length) : row.avance;
                this.actualizarTabla();
                this.calcularEstadisticasAvanzadas();
                this.showToast('Avance registrado', 'success');

                // Cerrar modal
                if (this.avanceModalInstance) {
                    this.avanceModalInstance.hide();
                }
                this.avanceDialogData = null;
            },
            error: () => this.showToast('No se pudo registrar el avance', 'error')
        });
    }

    onAvanceCancel() {
        if (this.avanceModalInstance) {
            this.avanceModalInstance.hide();
        }
        this.avanceDialogData = null;
    }

    private cargarAvancesParaTodos(slug: string) {
        const productos = this.pdmData?.planIndicativoProductos || [];
        if (!productos.length) return;

        const peticiones = productos.map(p =>
            this.pdmBackend.getAvances(slug, p.codigoIndicadorProducto).pipe(
                catchError(() => of(null))
            )
        );

        forkJoin(peticiones).pipe(takeUntil(this.destroy$)).subscribe((respuestas) => {
            respuestas.forEach((resp, idx) => {
                if (!resp) return;
                const row = productos[idx];
                if (!row.avances) row.avances = {};
                resp.avances.forEach(a => {
                    row.avances![a.anio] = {
                        valor: a.valor_ejecutado,
                        comentario: a.comentario
                    };
                });
                // Si no hay 'avance' global, establecemos promedio de años disponibles
                if (row.avance === undefined || row.avance === null) {
                    const vals = Object.values(row.avances).map(v => v.valor).filter(v => typeof v === 'number');
                    if (vals.length) {
                        row.avance = vals.reduce((a, b) => a + b, 0) / vals.length;
                    }
                }
            });
            this.actualizarTabla();
        });
    }

    calcularEstadisticasAvanzadas(): void {
        if (!this.productos.length) return;

        // Estadísticas por secretaría
        const secretariasMap = new Map<string, {
            totalMetas: number;
            avances: { 2024: number[]; 2025: number[]; 2026: number[]; 2027: number[] };
        }>();

        this.productos.forEach(p => {
            const sec = p.secretariaAsignada || 'Sin asignar';
            if (!secretariasMap.has(sec)) {
                secretariasMap.set(sec, {
                    totalMetas: 0,
                    avances: { 2024: [], 2025: [], 2026: [], 2027: [] }
                });
            }
            const stats = secretariasMap.get(sec)!;
            stats.totalMetas++;

            if (p.avances) {
                if (p.avances[2024]) stats.avances[2024].push(p.avances[2024].valor);
                if (p.avances[2025]) stats.avances[2025].push(p.avances[2025].valor);
                if (p.avances[2026]) stats.avances[2026].push(p.avances[2026].valor);
                if (p.avances[2027]) stats.avances[2027].push(p.avances[2027].valor);
            }
        });

        this.estadisticasPorSecretaria = Array.from(secretariasMap.entries()).map(([secretaria, stats]) => {
            const avg2024 = stats.avances[2024].length ? stats.avances[2024].reduce((a, b) => a + b, 0) / stats.avances[2024].length : 0;
            const avg2025 = stats.avances[2025].length ? stats.avances[2025].reduce((a, b) => a + b, 0) / stats.avances[2025].length : 0;
            const avg2026 = stats.avances[2026].length ? stats.avances[2026].reduce((a, b) => a + b, 0) / stats.avances[2026].length : 0;
            const avg2027 = stats.avances[2027].length ? stats.avances[2027].reduce((a, b) => a + b, 0) / stats.avances[2027].length : 0;
            const avancePromedio = (avg2024 + avg2025 + avg2026 + avg2027) / 4;

            return {
                secretaria,
                totalMetas: stats.totalMetas,
                avance2024: avg2024,
                avance2025: avg2025,
                avance2026: avg2026,
                avance2027: avg2027,
                avancePromedio
            };
        }).sort((a, b) => b.avancePromedio - a.avancePromedio);

        // Estadísticas por línea estratégica
        const lineasMap = new Map<string, {
            totalMetas: number;
            avances: { 2024: number[]; 2025: number[]; 2026: number[]; 2027: number[] };
        }>();

        this.productos.forEach(p => {
            const linea = p.lineaEstrategica || 'Sin definir';
            if (!lineasMap.has(linea)) {
                lineasMap.set(linea, {
                    totalMetas: 0,
                    avances: { 2024: [], 2025: [], 2026: [], 2027: [] }
                });
            }
            const stats = lineasMap.get(linea)!;
            stats.totalMetas++;

            if (p.avances) {
                if (p.avances[2024]) stats.avances[2024].push(p.avances[2024].valor);
                if (p.avances[2025]) stats.avances[2025].push(p.avances[2025].valor);
                if (p.avances[2026]) stats.avances[2026].push(p.avances[2026].valor);
                if (p.avances[2027]) stats.avances[2027].push(p.avances[2027].valor);
            }
        });

        this.estadisticasPorLinea = Array.from(lineasMap.entries()).map(([lineaEstrategica, stats]) => {
            const avg2024 = stats.avances[2024].length ? stats.avances[2024].reduce((a, b) => a + b, 0) / stats.avances[2024].length : 0;
            const avg2025 = stats.avances[2025].length ? stats.avances[2025].reduce((a, b) => a + b, 0) / stats.avances[2025].length : 0;
            const avg2026 = stats.avances[2026].length ? stats.avances[2026].reduce((a, b) => a + b, 0) / stats.avances[2026].length : 0;
            const avg2027 = stats.avances[2027].length ? stats.avances[2027].reduce((a, b) => a + b, 0) / stats.avances[2027].length : 0;
            const avancePromedio = (avg2024 + avg2025 + avg2026 + avg2027) / 4;

            return {
                lineaEstrategica,
                totalMetas: stats.totalMetas,
                avance2024: avg2024,
                avance2025: avg2025,
                avance2026: avg2026,
                avance2027: avg2027,
                avancePromedio
            };
        }).sort((a, b) => b.avancePromedio - a.avancePromedio);
    }

    ngOnDestroy(): void {
        this.destroy$.next();
        this.destroy$.complete();
    }

    aplicarFiltros(): void {
        this.actualizarTabla();
    }

    limpiarFiltros(): void {
        this.filtros = {};
        this.actualizarTabla();
    }

    private actualizarTabla(): void {
        this.productos = this.pdmService.obtenerDatosFiltrados(this.filtros);
        this.aplicarFiltroYOrdenamiento();
        this.calcularEstadisticasAvanzadas();
    }

    private aplicarFiltroYOrdenamiento(): void {
        let datos = [...this.productos];

        // Filtro de búsqueda
        const term = (this.searchTerm || '').trim().toLowerCase();
        if (term) {
            datos = datos.filter(data =>
                (data.personalizacion || '').toLowerCase().includes(term) ||
                (data.indicadorProducto || '').toLowerCase().includes(term) ||
                (data.sector || '').toLowerCase().includes(term) ||
                (data.lineaEstrategica || '').toLowerCase().includes(term) ||
                (data.secretariaAsignada || '').toLowerCase().includes(term)
            );
        }

        // Ordenamiento
        if (this.sortColumn) {
            datos.sort((a, b) => {
                const aVal = (a as any)[this.sortColumn];
                const bVal = (b as any)[this.sortColumn];
                const direction = this.sortDirection === 'asc' ? 1 : -1;
                if (aVal < bVal) return -1 * direction;
                if (aVal > bVal) return 1 * direction;
                return 0;
            });
        }

        this.productosFiltrados = datos;
    }

    onSort(column: string): void {
        if (this.sortColumn === column) {
            this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
        } else {
            this.sortColumn = column;
            this.sortDirection = 'asc';
        }
        this.aplicarFiltroYOrdenamiento();
    }

    onSearchChange(): void {
        this.currentPage = 1;
        this.aplicarFiltroYOrdenamiento();
    }

    get paginatedData(): PlanIndicativoProducto[] {
        const start = (this.currentPage - 1) * this.itemsPerPage;
        const end = start + this.itemsPerPage;
        return this.productosFiltrados.slice(start, end);
    }

    get totalPages(): number {
        return Math.ceil(this.productosFiltrados.length / this.itemsPerPage);
    }

    get pages(): number[] {
        return Array.from({ length: this.totalPages }, (_, i) => i + 1);
    }

    private generarGraficos(analisis: AnalisisPDM): void {
        // Gráfico de cumplimiento general (doughnut)
        this.chartCumplimiento = {
            labels: ['Cumplidas', 'En Progreso', 'Por Cumplir', 'Pendientes'],
            datasets: [{
                data: [
                    analisis.indicadoresGenerales.metasCumplidas,
                    analisis.indicadoresGenerales.metasEnProgreso,
                    analisis.indicadoresGenerales.metasPorCumplir,
                    analisis.indicadoresGenerales.metasPendientes
                ],
                backgroundColor: [
                    '#10b981',
                    '#3b82f6',
                    '#f59e0b',
                    '#ef4444'
                ],
                borderWidth: 3,
                borderColor: '#ffffff',
                hoverOffset: 8
            }]
        };

        // Gráfico por año (barras)
        this.chartPorAnio = {
            labels: analisis.analisisPorAnio.map(a => a.anio.toString()),
            datasets: [
                {
                    label: 'Total de Metas',
                    data: analisis.analisisPorAnio.map(a => a.totalMetas),
                    backgroundColor: 'rgba(59, 130, 246, 0.8)',
                    borderColor: '#3b82f6',
                    borderWidth: 1,
                    borderRadius: 8,
                    hoverBackgroundColor: '#3b82f6'
                },
                {
                    label: 'Metas Cumplidas',
                    data: analisis.analisisPorAnio.map(a => a.metasCumplidas),
                    backgroundColor: 'rgba(16, 185, 129, 0.8)',
                    borderColor: '#10b981',
                    borderWidth: 1,
                    borderRadius: 8,
                    hoverBackgroundColor: '#10b981'
                }
            ]
        };

        // Gráfico por sector (barras horizontales)
        const topSectores = analisis.analisisPorSector.slice(0, 10);
        this.chartPorSector = {
            labels: topSectores.map(s => this.truncarTexto(s.sector, 35)),
            datasets: [{
                label: '% Cumplimiento',
                data: topSectores.map(s => s.porcentajeCumplimiento),
                backgroundColor: topSectores.map(s => {
                    if (s.porcentajeCumplimiento >= 70) return 'rgba(16, 185, 129, 0.8)';
                    if (s.porcentajeCumplimiento >= 40) return 'rgba(245, 158, 11, 0.8)';
                    return 'rgba(239, 68, 68, 0.8)';
                }),
                borderColor: topSectores.map(s => {
                    if (s.porcentajeCumplimiento >= 70) return '#10b981';
                    if (s.porcentajeCumplimiento >= 40) return '#f59e0b';
                    return '#ef4444';
                }),
                borderWidth: 1,
                borderRadius: 8,
                hoverBackgroundColor: topSectores.map(s => {
                    if (s.porcentajeCumplimiento >= 70) return '#10b981';
                    if (s.porcentajeCumplimiento >= 40) return '#f59e0b';
                    return '#ef4444';
                })
            }]
        };

        // Gráfico de presupuesto por año (línea)
        this.chartPresupuesto = {
            labels: analisis.analisisPorAnio.map(a => a.anio.toString()),
            datasets: [{
                label: 'Presupuesto Total',
                data: analisis.analisisPorAnio.map(a => a.presupuestoTotal),
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                fill: true,
                tension: 0.4,
                pointBackgroundColor: '#3b82f6',
                pointBorderColor: '#ffffff',
                pointBorderWidth: 3,
                pointRadius: 6,
                pointHoverRadius: 8,
                borderWidth: 3
            }]
        };

        // Gráfico ODS - Distribución de metas
        if (analisis.analisisPorODS && analisis.analisisPorODS.length > 0) {
            this.chartODS = {
                labels: analisis.analisisPorODS.map(o => `ODS ${o.codigoODS}`),
                datasets: [{
                    data: analisis.analisisPorODS.map(o => o.totalMetas),
                    backgroundColor: [
                        '#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6',
                        '#1abc9c', '#34495e', '#e67e22', '#95a5a6', '#d35400',
                        '#c0392b', '#2980b9', '#27ae60', '#f1c40f', '#8e44ad',
                        '#16a085', '#2c3e50'
                    ],
                    borderWidth: 3,
                    borderColor: '#ffffff',
                    hoverOffset: 8
                }]
            };

            // Gráfico ODS - Top 5 por presupuesto
            const top5ODS = [...analisis.analisisPorODS]
                .sort((a, b) => b.presupuestoTotal - a.presupuestoTotal)
                .slice(0, 5);

            this.chartODSPresupuesto = {
                labels: top5ODS.map(o => `ODS ${o.codigoODS}`),
                datasets: [{
                    label: 'Presupuesto',
                    data: top5ODS.map(o => o.presupuestoTotal),
                    backgroundColor: 'rgba(16, 185, 129, 0.8)',
                    borderColor: '#10b981',
                    borderWidth: 1,
                    borderRadius: 8,
                    hoverBackgroundColor: '#10b981'
                }]
            };
        }

        // Gráfico SGR - Recursos por sector
        if (analisis.analisisSGR && analisis.analisisSGR.recursosSGRPorSector.length > 0) {
            const topSGR = analisis.analisisSGR.recursosSGRPorSector.slice(0, 8);
            this.chartSGRPorSector = {
                labels: topSGR.map(s => this.truncarTexto(s.sector, 30)),
                datasets: [{
                    label: 'Recursos SGR',
                    data: topSGR.map(s => s.totalRecursosSGR),
                    backgroundColor: 'rgba(245, 158, 11, 0.8)',
                    borderColor: '#f59e0b',
                    borderWidth: 1,
                    borderRadius: 8,
                    hoverBackgroundColor: '#f59e0b'
                }]
            };
        }

        // Gráfico Indicadores de Resultado - Alineación con PND
        if (analisis.analisisIndicadoresResultado) {
            this.chartIndicadoresPND = {
                labels: ['En PND', 'Fuera de PND'],
                datasets: [{
                    data: [
                        analisis.analisisIndicadoresResultado.indicadoresEnPND,
                        analisis.analisisIndicadoresResultado.indicadoresFueraPND
                    ],
                    backgroundColor: [
                        'rgba(16, 185, 129, 0.8)',
                        'rgba(156, 163, 175, 0.8)'
                    ],
                    borderColor: ['#10b981', '#9ca3af'],
                    borderWidth: 3,
                    hoverOffset: 8
                }]
            };

            // Gráfico Indicadores por Línea Estratégica
            if (analisis.analisisIndicadoresResultado.indicadoresPorLinea.length > 0) {
                const topLineas = analisis.analisisIndicadoresResultado.indicadoresPorLinea.slice(0, 8);
                this.chartIndicadoresPorLinea = {
                    labels: topLineas.map(l => this.truncarTexto(l.lineaEstrategica, 30)),
                    datasets: [
                        {
                            label: 'Total Indicadores',
                            data: topLineas.map(l => l.totalIndicadores),
                            backgroundColor: 'rgba(59, 130, 246, 0.8)',
                            borderColor: '#3b82f6',
                            borderWidth: 1,
                            borderRadius: 8,
                            hoverBackgroundColor: '#3b82f6'
                        },
                        {
                            label: 'Indicadores en PND',
                            data: topLineas.map(l => l.indicadoresEnPND),
                            backgroundColor: 'rgba(16, 185, 129, 0.8)',
                            borderColor: '#10b981',
                            borderWidth: 1,
                            borderRadius: 8,
                            hoverBackgroundColor: '#10b981'
                        }
                    ]
                };
            }
        }

        // Gráfico Presupuesto - Ordinario vs SGR
        if (analisis.analisisPresupuestoDetallado) {
            this.chartPresupuestoOrdinarioVsSGR = {
                labels: ['Recursos Ordinarios', 'Recursos SGR'],
                datasets: [{
                    data: [
                        analisis.analisisPresupuestoDetallado.presupuestoOrdinarioTotal,
                        analisis.analisisPresupuestoDetallado.presupuestoSGRTotal
                    ],
                    backgroundColor: [
                        'rgba(59, 130, 246, 0.8)',
                        'rgba(245, 158, 11, 0.8)'
                    ],
                    borderColor: ['#3b82f6', '#f59e0b'],
                    borderWidth: 3,
                    hoverOffset: 8
                }]
            };

            // Gráfico Presupuesto por Año Detallado (Ordinario + SGR)
            this.chartPresupuestoPorAnioDetallado = {
                labels: analisis.analisisPresupuestoDetallado.presupuestoPorAnio.map(p => p.anio.toString()),
                datasets: [
                    {
                        label: 'Ordinario',
                        data: analisis.analisisPresupuestoDetallado.presupuestoPorAnio.map(p => p.ordinario),
                        backgroundColor: 'rgba(59, 130, 246, 0.8)',
                        borderColor: '#3b82f6',
                        borderWidth: 1,
                        borderRadius: 8,
                        stack: 'stack0'
                    },
                    {
                        label: 'SGR',
                        data: analisis.analisisPresupuestoDetallado.presupuestoPorAnio.map(p => p.sgr),
                        backgroundColor: 'rgba(245, 158, 11, 0.8)',
                        borderColor: '#f59e0b',
                        borderWidth: 1,
                        borderRadius: 8,
                        stack: 'stack0'
                    }
                ]
            };

            // Gráfico Presupuesto por Sector Detallado (Top 8)
            const topSectoresPresupuesto = analisis.analisisPresupuestoDetallado.presupuestoPorSector.slice(0, 8);
            this.chartPresupuestoPorSectorDetallado = {
                labels: topSectoresPresupuesto.map(s => this.truncarTexto(s.sector, 30)),
                datasets: [
                    {
                        label: 'Ordinario',
                        data: topSectoresPresupuesto.map(s => s.ordinario),
                        backgroundColor: 'rgba(59, 130, 246, 0.8)',
                        borderColor: '#3b82f6',
                        borderWidth: 1,
                        borderRadius: 8
                    },
                    {
                        label: 'SGR',
                        data: topSectoresPresupuesto.map(s => s.sgr),
                        backgroundColor: 'rgba(245, 158, 11, 0.8)',
                        borderColor: '#f59e0b',
                        borderWidth: 1,
                        borderRadius: 8
                    }
                ]
            };
        }
    }

    truncarTexto(texto: string, maxLength: number): string {
        if (!texto) return '';
        return texto.length > maxLength ? texto.substring(0, maxLength) + '...' : texto;
    }

    formatearMoneda(valor: number): string {
        return new Intl.NumberFormat('es-CO', {
            style: 'currency',
            currency: 'COP',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(valor);
    }

    formatearPorcentaje(valor: number): string {
        return `${valor.toFixed(1)}%`;
    }

    obtenerColorEstado(estado: EstadoMeta | undefined): string {
        switch (estado) {
            case EstadoMeta.CUMPLIDA:
                return 'success';
            case EstadoMeta.EN_PROGRESO:
                return 'primary';
            case EstadoMeta.POR_CUMPLIR:
                return 'warn';
            case EstadoMeta.PENDIENTE:
                return 'accent';
            default:
                return '';
        }
    }

    obtenerEtiquetaEstado(estado: EstadoMeta | undefined): string {
        switch (estado) {
            case EstadoMeta.CUMPLIDA:
                return 'Cumplida';
            case EstadoMeta.EN_PROGRESO:
                return 'En Progreso';
            case EstadoMeta.POR_CUMPLIR:
                return 'Por Cumplir';
            case EstadoMeta.PENDIENTE:
                return 'Pendiente';
            case EstadoMeta.SIN_DEFINIR:
                return 'Sin Definir';
            default:
                return 'N/A';
        }
    }

    obtenerIconoTendencia(tipo: 'positivo' | 'neutro' | 'negativo'): string {
        switch (tipo) {
            case 'positivo':
                return 'trending_up';
            case 'negativo':
                return 'trending_down';
            default:
                return 'trending_flat';
        }
    }

    obtenerColorTendencia(tipo: 'positivo' | 'neutro' | 'negativo'): string {
        switch (tipo) {
            case 'positivo':
                return 'success';
            case 'negativo':
                return 'warn';
            default:
                return 'primary';
        }
    }

    cargarNuevoArchivo(): void {
        this.pdmService.limpiarDatos();
        this.router.navigate(['pdm-upload'], { relativeTo: this.router.routerState.root });
    }

    exportarDatos(): void {
        // TODO: Implementar exportación a PDF o Excel
        console.log('Exportar datos');
    }

    // Nuevas funciones para interactividad

    volverAlDashboard(): void {
        const slug = this.entityContext.currentEntity?.slug;
        if (slug) {
            this.router.navigate([`/${slug}/dashboard`]);
        } else {
            this.router.navigate(['/dashboard']);
        }
    }

    filtrarPorEstado(estado: string | undefined): void {
        if (estado === undefined) {
            this.filtros.estado = undefined;
        } else {
            this.filtros.estado = estado as EstadoMeta;
        }
        this.aplicarFiltros();
        // Scroll a la tabla
        const tableElement = document.querySelector('.table-responsive');
        if (tableElement) {
            tableElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }

    filtrarPorAnio(anio: number): void {
        this.filtros.anio = anio;
        this.aplicarFiltros();
        const tableElement = document.querySelector('.table-responsive');
        if (tableElement) tableElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    filtrarPorSecretaria(secretaria: string): void {
        this.filtros.secretaria = secretaria;
        this.aplicarFiltros();
        const tableElement = document.querySelector('.table-responsive');
        if (tableElement) tableElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    filtrarPorLinea(linea: string): void {
        this.filtros.lineaEstrategica = linea;
        this.aplicarFiltros();
        const tableElement = document.querySelector('.table-responsive');
        if (tableElement) tableElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    filtrarPorODS(codigoODS: string): void {
        this.filtros.ods = codigoODS;
        this.aplicarFiltros();
        const tableElement = document.querySelector('.table-responsive');
        if (tableElement) tableElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    verDetalleProducto(producto: PlanIndicativoProducto): void {
        this.productoSeleccionado = producto;
        this.cargarActividades();
    }

    cerrarDetalle(): void {
        this.productoSeleccionado = null;
        this.actividadesProducto = [];
    }

    abrirDialogoAvanceDesdeDetalle(): void {
        // Evita null: conserva la referencia antes de cerrar el modal
        const prod = this.productoSeleccionado;
        if (prod) {
            this.cerrarDetalle();
            this.abrirDialogoAvance(prod);
        }
    }

    // Gestión de actividades
    cargarActividades(): void {
        if (!this.productoSeleccionado) return;

        const slug = this.entityContext.currentEntity?.slug;
        if (!slug) return;

        this.cargandoActividades = true;
        this.pdmBackend.getActividades(slug, this.productoSeleccionado.codigoIndicadorProducto).subscribe({
            next: (response) => {
                this.actividadesProducto = response.actividades;
                this.cargandoActividades = false;
            },
            error: (error) => {
                console.error('Error al cargar actividades:', error);
                this.cargandoActividades = false;
                this.showToast('Error al cargar las actividades', 'error');
            }
        });
    }

    mostrarFormularioActividad(): void {
        this.actividadEditando = null;
        this.formActividad = {
            nombre: '',
            descripcion: '',
            responsable: '',
            fecha_inicio: '',
            fecha_fin: '',
            porcentaje_avance: 0,
            estado: 'pendiente'
        };
        this.mostrandoFormActividad = true;
    }

    editarActividad(actividad: any): void {
        this.actividadEditando = actividad;
        this.formActividad = {
            nombre: actividad.nombre,
            descripcion: actividad.descripcion || '',
            responsable: actividad.responsable || '',
            fecha_inicio: actividad.fecha_inicio ? actividad.fecha_inicio.split('T')[0] : '',
            fecha_fin: actividad.fecha_fin ? actividad.fecha_fin.split('T')[0] : '',
            porcentaje_avance: actividad.porcentaje_avance,
            estado: actividad.estado
        };
        this.mostrandoFormActividad = true;
    }

    cerrarFormularioActividad(): void {
        this.mostrandoFormActividad = false;
        this.actividadEditando = null;
    }

    guardarActividad(): void {
        if (!this.formActividad.nombre || !this.productoSeleccionado) return;

        const slug = this.entityContext.currentEntity?.slug;
        if (!slug) return;

        this.guardandoActividad = true;

        const payload = {
            ...this.formActividad,
            codigo_indicador_producto: this.productoSeleccionado.codigoIndicadorProducto
        };

        const request = this.actividadEditando
            ? this.pdmBackend.updateActividad(slug, this.actividadEditando.id, payload)
            : this.pdmBackend.createActividad(slug, payload);

        request.subscribe({
            next: () => {
                this.showToast(
                    this.actividadEditando ? 'Actividad actualizada exitosamente' : 'Actividad creada exitosamente',
                    'success'
                );
                this.cerrarFormularioActividad();
                this.cargarActividades();
                this.guardandoActividad = false;
            },
            error: (error) => {
                console.error('Error al guardar actividad:', error);
                this.showToast('Error al guardar la actividad', 'error');
                this.guardandoActividad = false;
            }
        });
    }

    eliminarActividad(actividad: any): void {
        if (!confirm(`¿Está seguro de eliminar la actividad "${actividad.nombre}"?`)) return;

        const slug = this.entityContext.currentEntity?.slug;
        if (!slug) return;

        this.pdmBackend.deleteActividad(slug, actividad.id).subscribe({
            next: () => {
                this.showToast('Actividad eliminada exitosamente', 'success');
                this.cargarActividades();
            },
            error: (error) => {
                console.error('Error al eliminar actividad:', error);
                this.showToast('Error al eliminar la actividad', 'error');
            }
        });
    }

    obtenerEtiquetaEstadoActividad(estado: string): string {
        const etiquetas: Record<string, string> = {
            'pendiente': 'Pendiente',
            'en_progreso': 'En Progreso',
            'completada': 'Completada',
            'cancelada': 'Cancelada'
        };
        return etiquetas[estado] || estado;
    }

    formatearFecha(fecha: string): string {
        if (!fecha) return '';
        const date = new Date(fecha);
        return date.toLocaleDateString('es-CO', { year: 'numeric', month: 'short', day: 'numeric' });
    }

    // Validaciones de formulario de actividad
    validFechaRango(): boolean {
        const inicio = this.formActividad.fecha_inicio;
        const fin = this.formActividad.fecha_fin;
        if (!inicio || !fin) return true; // si falta una, no invalida
        try {
            const d1 = new Date(inicio + 'T00:00:00');
            const d2 = new Date(fin + 'T00:00:00');
            return d1.getTime() <= d2.getTime();
        } catch {
            return true;
        }
    }

    fechasCompletas(): boolean {
        const inicio = this.formActividad.fecha_inicio;
        const fin = this.formActividad.fecha_fin;
        // ambas vacías o ambas con valor
        return (!inicio && !fin) || (!!inicio && !!fin);
    }

    validActividadForm(): boolean {
        const nombreOk = !!(this.formActividad.nombre && this.formActividad.nombre.trim());
        const avance = Number(this.formActividad.porcentaje_avance ?? 0);
        const avanceOk = avance >= 0 && avance <= 100;
        const fechasOk = this.validFechaRango() && this.fechasCompletas();
        const responsableOk = !!(this.formActividad.responsable && this.formActividad.responsable.trim());
        return nombreOk && responsableOk && avanceOk && fechasOk;
    }
}
