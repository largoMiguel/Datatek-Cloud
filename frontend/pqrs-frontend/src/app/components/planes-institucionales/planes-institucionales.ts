import { Component, OnInit, OnDestroy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { Location } from '@angular/common';
import { PlanInstitucional, Meta, CreateMetaRequest } from '../../models/plan.model';
import { AiService, PlanAnalysisRequest } from '../../services/ai.service';
import { PlanReportService } from '../../services/plan-report.service';
import { PlanService } from '../../services/plan.service';
import { AlertService } from '../../services/alert.service';
import { AuthService } from '../../services/auth.service';
import { User } from '../../models/user.model';

@Component({
    selector: 'app-planes-institucionales',
    standalone: true,
    imports: [CommonModule, FormsModule],
    templateUrl: './planes-institucionales.html',
    styleUrls: ['./planes-institucionales.scss']
})
export class PlanesInstitucionalesComponent implements OnInit, OnDestroy {
    private router = inject(Router);
    private location = inject(Location);
    private aiService = inject(AiService);
    private planReportService = inject(PlanReportService);
    private planService = inject(PlanService);
    private alertService = inject(AlertService);
    private authService = inject(AuthService);

    planes: PlanInstitucional[] = [];
    metasPorPlan: Map<number, Meta[]> = new Map();
    currentUser: User | null = null;

    vistaActual: 'planes' | 'metas' | 'analytics' = 'planes';
    vistaAnterior: 'planes' | 'metas' | 'analytics' = 'planes';
    planSeleccionado: PlanInstitucional | null = null;
    private popstateListener: any;

    // Lista de secretarías
    secretarias: string[] = [
        'Secretaría de Gobierno',
        'Secretaría de Hacienda',
        'Secretaría de Planeación',
        'Secretaría de Obras Públicas',
        'Secretaría de Educación',
        'Secretaría de Salud',
        'Secretaría de Desarrollo Social',
        'Secretaría de Medio Ambiente',
        'Secretaría de Cultura',
        'Secretaría de Deportes'
    ];

    // Modales
    mostrarModalPlan = false;
    mostrarModalMeta = false;
    modoEdicion = false;

    // Formularios
    planForm: PlanInstitucional = this.inicializarPlanForm();
    metaForm: Meta = this.inicializarMetaForm();

    // Filtros
    filtroEstadoPlan: string = '';
    filtroAnio: number | null = null;
    filtroEstadoMeta: string = '';

    // Generación de informes
    generandoInforme = false;
    mostrarSelectorFechasInforme = false;
    fechaInicioInforme: string = '';
    fechaFinInforme: string = '';
    planParaInforme: PlanInstitucional | null = null;

    // Analytics
    analyticsData: any = null;

    ngOnInit(): void {
        // Obtener usuario actual PRIMERO antes de cargar planes
        this.authService.currentUser$.subscribe(user => {
            this.currentUser = user;
            console.log('=== NGONINIT - USUARIO CARGADO ===');
            console.log('Usuario completo:', JSON.stringify(user, null, 2));
            console.log('user.secretaria (valor exacto):', `[${user?.secretaria}]`);
            console.log('user.secretaria (length):', user?.secretaria?.length);
            console.log('user.role:', user?.role);
            console.log('===================================');

            // Cargar planes DESPUÉS de tener el usuario
            this.cargarPlanes();
        });
        this.setupPopstateListener();
    }

    ngOnDestroy(): void {
        // Limpiar el listener del historial al salir del componente
        window.removeEventListener('popstate', this.handlePopstate);
    }

    private handlePopstate = (event: PopStateEvent): void => {
        // Solo manejar si estamos dentro del componente y no en la vista principal de planes
        if (this.vistaActual !== 'planes') {
            // Prevenir la navegación y manejar internamente
            this.volverVistaAnterior();
            // Volver a agregar estado para mantener el componente activo
            history.pushState(null, '', window.location.href);
        }
    };

    setupPopstateListener(): void {
        // Escuchar el evento popstate del navegador
        window.addEventListener('popstate', this.handlePopstate);
        // Agregar estado inicial
        history.pushState(null, '', window.location.href);
    }

    inicializarPlanForm(): PlanInstitucional {
        const anioActual = new Date().getFullYear();
        return {
            nombre: '',
            descripcion: '',
            anio: anioActual,
            fecha_inicio: '',
            fecha_fin: '',
            estado: 'activo'
        };
    }

    inicializarMetaForm(): Meta {
        return {
            nombre: '',
            descripcion: '',
            indicador: '',
            meta_numerica: 100,
            avance_actual: 0,
            fecha_inicio: '',
            fecha_fin: '',
            responsable: '',
            estado: 'no_iniciada',
            resultado: ''
        };
    }

    cargarPlanes(): void {
        console.log('=== CARGANDO PLANES DESDE BACKEND ===');

        this.planService.getPlanes(this.filtroAnio || undefined, this.filtroEstadoPlan || undefined)
            .subscribe({
                next: (planes) => {
                    this.planes = planes;
                    console.log('Planes cargados desde backend:', planes.length);

                    // Si no hay planes, no hay metas que verificar
                    if (planes.length === 0) {
                        return;
                    }

                    // Contador para saber cuándo terminamos de cargar todas las metas
                    let planesConMetasCargadas = 0;
                    const totalPlanes = planes.filter(p => p.id).length;

                    // Cargar metas para cada plan
                    planes.forEach(plan => {
                        if (plan.id) {
                            this.cargarMetasDePlan(plan.id, () => {
                                planesConMetasCargadas++;
                                // Cuando terminemos de cargar todas las metas, verificar alertas
                                if (planesConMetasCargadas === totalPlanes) {
                                    this.verificarMetasProximasVencer();
                                }
                            });
                        }
                    });
                },
                error: (error) => {
                    console.error('Error al cargar planes:', error);
                    this.alertService.error('Error al cargar los planes institucionales');
                    this.planes = [];
                }
            });

        console.log('Usuario actual:', this.currentUser);
        console.log('Rol:', this.currentUser?.role);
        console.log('Secretaría:', this.currentUser?.secretaria);
    }

    /**
     * Cargar metas de un plan específico desde el backend
     */
    private cargarMetasDePlan(planId: number, onComplete?: () => void): void {
        this.planService.getMetasByPlan(planId, this.filtroEstadoMeta || undefined)
            .subscribe({
                next: (metas) => {
                    this.metasPorPlan.set(planId, metas);
                    console.log(`Metas del plan ${planId} cargadas:`, metas.length);
                    // Llamar al callback si existe
                    if (onComplete) {
                        onComplete();
                    }
                },
                error: (error) => {
                    console.error(`Error al cargar metas del plan ${planId}:`, error);
                    this.metasPorPlan.set(planId, []);
                    // Llamar al callback incluso en error para no bloquear el contador
                    if (onComplete) {
                        onComplete();
                    }
                }
            });
    }    // Gestión de vistas
    verMetas(plan: PlanInstitucional): void {
        console.log('=== VER METAS DEL PLAN ===');
        console.log('Plan seleccionado:', plan.nombre);
        console.log('Usuario actual:', this.currentUser?.username);
        console.log('Secretaría:', `[${this.currentUser?.secretaria}]`);
        console.log('Role:', this.currentUser?.role);

        this.vistaAnterior = this.vistaActual;
        this.planSeleccionado = plan;
        this.vistaActual = 'metas';
    }

    volverAPlanes(): void {
        this.vistaActual = 'planes';
        this.vistaAnterior = 'planes';
        this.planSeleccionado = null;
        this.analyticsData = null;
    }

    volverVistaAnterior(): void {
        // Si estamos en analytics o metas y la vista anterior es planes, simplemente volver a planes
        if ((this.vistaActual === 'analytics' || this.vistaActual === 'metas') && this.vistaAnterior === 'planes') {
            this.volverAPlanes();
            return;
        }

        // Si estamos en analytics y veníamos de metas, volver a metas
        if (this.vistaActual === 'analytics' && this.vistaAnterior === 'metas') {
            this.vistaActual = 'metas';
            this.vistaAnterior = 'planes'; // Actualizar para que el siguiente "volver" funcione
            return;
        }

        // Si estamos en metas y veníamos de analytics, volver a analytics
        if (this.vistaActual === 'metas' && this.vistaAnterior === 'analytics') {
            this.vistaActual = 'analytics';
            this.vistaAnterior = 'planes'; // Actualizar para que el siguiente "volver" funcione
            return;
        }

        // Comportamiento por defecto - volver a planes
        this.volverAPlanes();
    }

    verAnalytics(plan: PlanInstitucional): void {
        this.vistaAnterior = this.vistaActual;
        this.planSeleccionado = plan;
        this.vistaActual = 'analytics';
        this.calcularAnalytics();
    }

    // Filtrar metas por estado desde las tarjetas de analytics
    filtrarMetasPorEstado(estado: string): void {
        if (!this.planSeleccionado) return;

        // Limpiar filtro de estado
        this.filtroEstadoMeta = '';

        // Aplicar el nuevo filtro de estado (string vacío = todas)
        if (estado) {
            this.filtroEstadoMeta = estado;
        }

        // Cambiar a la vista de metas
        this.vistaAnterior = 'analytics';
        this.vistaActual = 'metas';
    }

    calcularAnalytics(): void {
        if (!this.planSeleccionado?.id) return;

        const metas = this.getMetasDePlan(this.planSeleccionado.id);
        const totalMetas = metas.length;

        if (totalMetas === 0) {
            this.analyticsData = null;
            return;
        }

        const metasCompletadas = metas.filter(m => m.estado === 'completada').length;
        const metasEnProgreso = metas.filter(m => m.estado === 'en_progreso').length;
        const metasAtrasadas = metas.filter(m => m.estado === 'atrasada').length;
        const metasNoIniciadas = metas.filter(m => m.estado === 'no_iniciada').length;

        const avanceGlobal = Math.round(
            metas.reduce((sum, m) => sum + this.getPorcentajeAvance(m), 0) / totalMetas
        );

        // Agrupar por responsable
        const metasPorResponsable: { [key: string]: number } = {};
        metas.forEach(m => {
            metasPorResponsable[m.responsable] = (metasPorResponsable[m.responsable] || 0) + 1;
        });

        // Calcular tiempo restante promedio
        const hoy = new Date();
        const tiemposRestantes = metas
            .filter(m => m.estado !== 'completada')
            .map(m => {
                const fechaFin = new Date(m.fecha_fin);
                const dias = Math.ceil((fechaFin.getTime() - hoy.getTime()) / (1000 * 60 * 60 * 24));
                return dias;
            });

        const tiempoPromedioRestante = tiemposRestantes.length > 0
            ? Math.round(tiemposRestantes.reduce((sum, t) => sum + t, 0) / tiemposRestantes.length)
            : 0;

        const metasConResultado = metas.filter(m => m.resultado && m.resultado.trim() !== '').length;

        this.analyticsData = {
            totalMetas,
            metasCompletadas,
            metasEnProgreso,
            metasAtrasadas,
            metasNoIniciadas,
            avanceGlobal,
            porcentajeCompletadas: Math.round((metasCompletadas / totalMetas) * 100),
            porcentajeEnProgreso: Math.round((metasEnProgreso / totalMetas) * 100),
            porcentajeAtrasadas: Math.round((metasAtrasadas / totalMetas) * 100),
            porcentajeNoIniciadas: Math.round((metasNoIniciadas / totalMetas) * 100),
            metasPorResponsable,
            tiempoPromedioRestante,
            metasConResultado,
            porcentajeConResultado: Math.round((metasConResultado / totalMetas) * 100)
        };
    }

    // CRUD Planes
    abrirModalNuevoPlan(): void {
        if (!this.canCreatePlanes()) {
            this.alertService.error('No tiene permisos para crear planes');
            return;
        }
        this.modoEdicion = false;
        this.planForm = this.inicializarPlanForm();
        this.mostrarModalPlan = true;
    }

    abrirModalEditarPlan(plan: PlanInstitucional): void {
        if (!this.canEditPlan(plan)) {
            this.alertService.error('No tiene permisos para editar este plan');
            return;
        }
        this.modoEdicion = true;
        this.planForm = { ...plan };
        this.mostrarModalPlan = true;
    }

    guardarPlan(): void {
        console.log('=== GUARDANDO PLAN ===');
        console.log('Plan Form:', this.planForm);
        console.log('Modo Edición:', this.modoEdicion);

        if (!this.canCreatePlanes() && !this.modoEdicion) {
            this.alertService.error('No tiene permisos para crear planes');
            return;
        }

        // Validar campos requeridos
        if (!this.planForm.nombre || this.planForm.nombre.trim().length < 3) {
            this.alertService.error('El nombre del plan debe tener al menos 3 caracteres');
            return;
        }

        if (!this.planForm.descripcion || this.planForm.descripcion.trim().length < 10) {
            this.alertService.error('La descripción debe tener al menos 10 caracteres');
            return;
        }

        if (!this.planForm.anio || this.planForm.anio < 2020 || this.planForm.anio > 2030) {
            this.alertService.error('El año debe estar entre 2020 y 2030');
            return;
        }

        if (!this.planForm.fecha_inicio) {
            this.alertService.error('La fecha de inicio es obligatoria');
            return;
        }

        if (!this.planForm.fecha_fin) {
            this.alertService.error('La fecha de fin es obligatoria');
            return;
        }

        // Validar que fecha_fin sea posterior a fecha_inicio
        if (new Date(this.planForm.fecha_inicio) >= new Date(this.planForm.fecha_fin)) {
            this.alertService.error('La fecha de fin debe ser posterior a la fecha de inicio');
            return;
        }

        if (!this.planForm.estado) {
            this.alertService.error('Debe seleccionar un estado para el plan');
            return;
        }

        if (this.modoEdicion) {
            // Actualizar plan existente
            if (!this.planForm.id) return;

            console.log('Actualizando plan ID:', this.planForm.id);
            this.planService.updatePlan(this.planForm.id, this.planForm).subscribe({
                next: (planActualizado) => {
                    const index = this.planes.findIndex(p => p.id === planActualizado.id);
                    if (index !== -1) {
                        this.planes[index] = planActualizado;
                    }
                    this.alertService.success('Plan actualizado correctamente');
                    this.cerrarModalPlan();
                },
                error: (error) => {
                    console.error('Error al actualizar plan:', error);
                    this.alertService.error(error.error?.detail || 'Error al actualizar el plan');
                }
            });
        } else {
            // Crear nuevo plan
            console.log('Creando nuevo plan...');
            this.planService.createPlan(this.planForm).subscribe({
                next: (nuevoPlan) => {
                    console.log('Plan creado exitosamente:', nuevoPlan);
                    this.planes.push(nuevoPlan);
                    if (nuevoPlan.id) {
                        this.metasPorPlan.set(nuevoPlan.id, []);
                    }
                    this.alertService.success('Plan creado correctamente');
                    this.cerrarModalPlan();
                },
                error: (error) => {
                    console.error('Error al crear plan:', error);
                    console.error('Detalles del error:', error.error);

                    let mensajeError = 'Error al crear el plan';
                    if (error.error?.detail) {
                        if (Array.isArray(error.error.detail)) {
                            const errores = error.error.detail.map((e: any) =>
                                `${e.loc?.join('.')} - ${e.msg}`
                            ).join(', ');
                            mensajeError = `Validación: ${errores}`;
                        } else if (typeof error.error.detail === 'string') {
                            mensajeError = error.error.detail;
                        }
                    }
                    this.alertService.error(mensajeError);
                }
            });
        }
    }

    eliminarPlan(plan: PlanInstitucional): void {
        if (!plan.id) return;

        if (confirm(`¿Está seguro de eliminar el plan "${plan.nombre}"? Se eliminarán también todas sus metas.`)) {
            this.planService.deletePlan(plan.id).subscribe({
                next: () => {
                    this.planes = this.planes.filter(p => p.id !== plan.id);
                    this.metasPorPlan.delete(plan.id!);
                    this.alertService.success('Plan eliminado correctamente');
                },
                error: (error) => {
                    console.error('Error al eliminar plan:', error);
                    this.alertService.error(error.error?.detail || 'Error al eliminar el plan');
                }
            });
        }
    }

    cerrarModalPlan(): void {
        this.mostrarModalPlan = false;
        this.planForm = this.inicializarPlanForm();
    }

    // CRUD Metas
    abrirModalNuevaMeta(): void {
        if (!this.canCreateMetas()) {
            this.alertService.error('No tiene permisos para crear metas');
            return;
        }
        if (!this.planSeleccionado?.id) return;
        this.modoEdicion = false;
        this.metaForm = this.inicializarMetaForm();
        this.metaForm.plan_id = this.planSeleccionado.id;
        this.mostrarModalMeta = true;
    }

    abrirModalEditarMeta(meta: Meta): void {
        if (!this.canEditMeta(meta)) {
            this.alertService.error('No tiene permisos para editar esta meta');
            return;
        }
        this.modoEdicion = true;
        this.metaForm = { ...meta };
        this.mostrarModalMeta = true;
    }

    guardarMeta(): void {
        if (!this.planSeleccionado?.id) return;

        console.log('=== GUARDANDO META EN BACKEND ===');
        console.log('Meta Form:', this.metaForm);
        console.log('Responsable:', this.metaForm.responsable);

        if (this.modoEdicion) {
            // Actualizar meta existente
            if (!this.metaForm.id) return;

            if (!this.canEditMeta(this.metaForm)) {
                this.alertService.error('No tiene permisos para editar esta meta');
                return;
            }

            // Validar campos antes de actualizar
            if (this.metaForm.nombre && this.metaForm.nombre.length < 3) {
                this.alertService.error('El nombre debe tener al menos 3 caracteres');
                return;
            }

            if (this.metaForm.descripcion && this.metaForm.descripcion.length < 10) {
                this.alertService.error('La descripción debe tener al menos 10 caracteres');
                return;
            }

            if (this.metaForm.indicador && this.metaForm.indicador.length < 3) {
                this.alertService.error('El indicador debe tener al menos 3 caracteres');
                return;
            }

            if (this.metaForm.meta_numerica && this.metaForm.meta_numerica <= 0) {
                this.alertService.error('La meta numérica debe ser mayor que 0');
                return;
            }

            if (this.metaForm.avance_actual > this.metaForm.meta_numerica) {
                this.alertService.error('El avance actual no puede ser mayor que la meta numérica');
                return;
            }

            this.planService.updateMeta(this.metaForm.id, this.metaForm).subscribe({
                next: (metaActualizada) => {
                    // Actualizar en el Map local
                    const metas = this.metasPorPlan.get(this.planSeleccionado!.id!) || [];
                    const index = metas.findIndex(m => m.id === metaActualizada.id);
                    if (index !== -1) {
                        metas[index] = metaActualizada;
                        this.metasPorPlan.set(this.planSeleccionado!.id!, metas);
                    }

                    this.alertService.success('Meta actualizada correctamente');
                    this.cerrarModalMeta();
                },
                error: (error) => {
                    console.error('Error al actualizar meta:', error);
                    console.error('Detalles del error:', error.error);

                    // Mostrar mensaje de error detallado
                    let mensajeError = 'Error al actualizar la meta';
                    if (error.error?.detail) {
                        if (Array.isArray(error.error.detail)) {
                            const errores = error.error.detail.map((e: any) =>
                                `${e.loc?.join('.')} - ${e.msg}`
                            ).join(', ');
                            mensajeError = `Validación: ${errores}`;
                        } else if (typeof error.error.detail === 'string') {
                            mensajeError = error.error.detail;
                        } else {
                            mensajeError = JSON.stringify(error.error.detail);
                        }
                    }

                    this.alertService.error(mensajeError);
                }
            });
        } else {
            // Crear nueva meta
            if (!this.canCreateMetas()) {
                this.alertService.error('No tiene permisos para crear metas');
                return;
            }

            // Validar campos requeridos
            if (!this.metaForm.nombre || !this.metaForm.descripcion || !this.metaForm.indicador) {
                this.alertService.error('Complete todos los campos obligatorios');
                return;
            }

            // Validar longitud mínima de campos
            if (this.metaForm.nombre.length < 3) {
                this.alertService.error('El nombre debe tener al menos 3 caracteres');
                return;
            }

            if (this.metaForm.descripcion.length < 10) {
                this.alertService.error('La descripción debe tener al menos 10 caracteres');
                return;
            }

            if (this.metaForm.indicador.length < 3) {
                this.alertService.error('El indicador debe tener al menos 3 caracteres');
                return;
            }

            if (!this.metaForm.fecha_inicio || !this.metaForm.fecha_fin) {
                this.alertService.error('Las fechas de inicio y fin son obligatorias');
                return;
            }

            if (!this.metaForm.responsable) {
                this.alertService.error('Debe seleccionar una secretaría responsable');
                return;
            }

            // Validar que meta_numerica sea mayor que 0
            if (this.metaForm.meta_numerica <= 0) {
                this.alertService.error('La meta numérica debe ser mayor que 0');
                return;
            }

            // Validar que avance_actual no sea mayor que meta_numerica
            if (this.metaForm.avance_actual > this.metaForm.meta_numerica) {
                this.alertService.error('El avance actual no puede ser mayor que la meta numérica');
                return;
            }

            // Preparar datos para enviar
            const metaData: CreateMetaRequest = {
                nombre: this.metaForm.nombre,
                descripcion: this.metaForm.descripcion,
                indicador: this.metaForm.indicador,
                meta_numerica: this.metaForm.meta_numerica,
                avance_actual: this.metaForm.avance_actual,
                fecha_inicio: this.metaForm.fecha_inicio,
                fecha_fin: this.metaForm.fecha_fin,
                responsable: this.metaForm.responsable,
                estado: this.metaForm.estado,
                resultado: this.metaForm.resultado,
                plan_id: this.planSeleccionado.id
            };

            console.log('Datos a enviar:', JSON.stringify(metaData, null, 2));

            this.planService.createMeta(this.planSeleccionado.id, metaData).subscribe({
                next: (nuevaMeta) => {
                    // Agregar al Map local
                    const metas = this.metasPorPlan.get(this.planSeleccionado!.id!) || [];
                    metas.push(nuevaMeta);
                    this.metasPorPlan.set(this.planSeleccionado!.id!, metas);

                    console.log('Meta creada:', nuevaMeta);
                    this.alertService.success('Meta creada correctamente');
                    this.cerrarModalMeta();
                },
                error: (error) => {
                    console.error('Error al crear meta:', error);
                    console.error('Detalles del error:', error.error);

                    // Mostrar mensaje de error detallado
                    let mensajeError = 'Error al crear la meta';
                    if (error.error?.detail) {
                        if (Array.isArray(error.error.detail)) {
                            // Errores de validación de Pydantic
                            const errores = error.error.detail.map((e: any) =>
                                `${e.loc?.join('.')} - ${e.msg}`
                            ).join(', ');
                            mensajeError = `Validación: ${errores}`;
                        } else if (typeof error.error.detail === 'string') {
                            mensajeError = error.error.detail;
                        } else {
                            mensajeError = JSON.stringify(error.error.detail);
                        }
                    }

                    this.alertService.error(mensajeError);
                }
            });
        }
    }

    eliminarMeta(meta: Meta): void {
        if (!this.planSeleccionado?.id || !meta.id) return;

        if (!this.canDeleteMeta(meta)) {
            this.alertService.error('No tiene permisos para eliminar esta meta');
            return;
        }

        if (confirm(`¿Está seguro de eliminar la meta "${meta.nombre}"?`)) {
            this.planService.deleteMeta(meta.id).subscribe({
                next: () => {
                    // Eliminar del Map local
                    const metas = this.metasPorPlan.get(this.planSeleccionado!.id!) || [];
                    const metasActualizadas = metas.filter(m => m.id !== meta.id);
                    this.metasPorPlan.set(this.planSeleccionado!.id!, metasActualizadas);

                    this.alertService.success('Meta eliminada correctamente');
                },
                error: (error) => {
                    console.error('Error al eliminar meta:', error);
                    this.alertService.error(error.error?.detail || 'Error al eliminar la meta');
                }
            });
        }
    }

    cerrarModalMeta(): void {
        this.mostrarModalMeta = false;
        this.metaForm = this.inicializarMetaForm();
    }

    // Utilidades
    getMetasDePlan(planId: number): Meta[] {
        const todasLasMetas = this.metasPorPlan.get(planId) || [];

        console.log('=== GETMETASDEPLAN - DEBUG DETALLADO ===');
        console.log('Total de metas en el plan:', todasLasMetas.length);
        console.log('Usuario actual completo:', JSON.stringify(this.currentUser, null, 2));
        console.log('currentUser.secretaria (valor exacto):', `[${this.currentUser?.secretaria}]`);
        console.log('currentUser.secretaria (length):', this.currentUser?.secretaria?.length);
        console.log('Es admin:', this.isAdmin());
        console.log('Es secretario:', this.isSecretario());

        // Si es admin, mostrar todas las metas
        if (this.isAdmin()) {
            console.log('Admin - Mostrando todas las metas:', todasLasMetas.length);
            return todasLasMetas;
        }

        // Si es secretario, mostrar solo sus metas
        if (this.isSecretario() && this.currentUser?.secretaria) {
            console.log('Filtrando metas para secretario...');
            const metasFiltradas = todasLasMetas.filter(meta => {
                const responsable = meta.responsable;
                const secretaria = this.currentUser?.secretaria;
                const sonIguales = responsable === secretaria;

                console.log(`  Meta: "${meta.nombre}"`);
                console.log(`    responsable: [${responsable}] (length: ${responsable?.length})`);
                console.log(`    secretaria:  [${secretaria}] (length: ${secretaria?.length})`);
                console.log(`    ¿Son iguales?: ${sonIguales}`);

                return sonIguales;
            });
            console.log('Secretario - Metas filtradas:', metasFiltradas.length);
            console.log('Metas encontradas:', metasFiltradas.map(m => m.nombre));
            return metasFiltradas;
        }

        console.log('Sin permisos - Retornando array vacío');
        return [];
    }

    // Métodos de permisos
    isAdmin(): boolean {
        return this.currentUser?.role === 'admin';
    }

    isSecretario(): boolean {
        return this.currentUser?.role === 'secretario';
    }

    canCreatePlanes(): boolean {
        return this.isAdmin();
    }

    canEditPlan(plan: PlanInstitucional): boolean {
        return this.isAdmin();
    }

    canDeletePlan(plan: PlanInstitucional): boolean {
        return this.isAdmin();
    }

    canCreateMetas(): boolean {
        return this.isAdmin();
    }

    canEditMeta(meta: Meta): boolean {
        if (this.isAdmin()) return true;
        if (this.isSecretario() && this.currentUser?.secretaria) {
            return meta.responsable === this.currentUser.secretaria;
        }
        return false;
    }

    canDeleteMeta(meta: Meta): boolean {
        return this.isAdmin();
    }

    canViewAnalytics(): boolean {
        // Tanto admin como secretario pueden ver analytics
        return this.isAdmin() || this.isSecretario();
    }

    canGenerateReport(): boolean {
        // Tanto admin como secretario pueden generar informes
        return this.isAdmin() || this.isSecretario();
    }

    // Exponer Object para el template
    Object = Object;

    // Método auxiliar para obtener las entradas del diccionario con tipos correctos
    getMetasEntries(dict: { [key: string]: number }): [string, number][] {
        return Object.entries(dict) as [string, number][];
    }

    getPlanesVisibles(): PlanInstitucional[] {
        let planesFiltrados = [...this.planes];

        if (this.filtroEstadoPlan) {
            planesFiltrados = planesFiltrados.filter(p => p.estado === this.filtroEstadoPlan);
        }

        if (this.filtroAnio) {
            planesFiltrados = planesFiltrados.filter(p => p.anio === this.filtroAnio);
        }

        return planesFiltrados;
    }

    getMetasVisibles(): Meta[] {
        if (!this.planSeleccionado?.id) return [];

        let metas = this.getMetasDePlan(this.planSeleccionado.id);

        if (this.filtroEstadoMeta) {
            metas = metas.filter(m => m.estado === this.filtroEstadoMeta);
        }

        return metas;
    }

    getPorcentajeAvance(meta: Meta): number {
        if (meta.meta_numerica === 0) return 0;
        return Math.min(100, Math.round((meta.avance_actual / meta.meta_numerica) * 100));
    }

    getEstadoColor(estado: string): string {
        const colores: { [key: string]: string } = {
            'activo': 'success',
            'finalizado': 'secondary',
            'suspendido': 'warning',
            'no_iniciada': 'secondary',
            'en_progreso': 'primary',
            'completada': 'success',
            'atrasada': 'danger'
        };
        return colores[estado] || 'secondary';
    }

    getEstadoTexto(estado: string): string {
        const textos: { [key: string]: string } = {
            'activo': 'Activo',
            'finalizado': 'Finalizado',
            'suspendido': 'Suspendido',
            'no_iniciada': 'No Iniciada',
            'en_progreso': 'En Progreso',
            'completada': 'Completada',
            'atrasada': 'Atrasada'
        };
        return textos[estado] || estado;
    }

    limpiarFiltros(): void {
        this.filtroEstadoPlan = '';
        this.filtroAnio = null;
        this.filtroEstadoMeta = '';
    }

    volver(): void {
        this.router.navigate(['/dashboard']);
    }

    getAniosDisponibles(): number[] {
        const anioActual = new Date().getFullYear();
        const anios: number[] = [];
        for (let i = anioActual - 2; i <= anioActual + 2; i++) {
            anios.push(i);
        }
        return anios;
    }

    /**
     * Genera un informe PDF completo del plan seleccionado
     */
    // Mostrar formulario para seleccionar fechas del informe
    mostrarFormularioInforme(plan: PlanInstitucional): void {
        if (!plan.id) {
            this.alertService.error('No se puede generar el informe de un plan sin ID', 'Error');
            return;
        }

        // Verificar que hay metas
        const metas = this.getMetasDePlan(plan.id);
        if (metas.length === 0) {
            this.alertService.warning(
                'El plan no tiene metas registradas. Agregue metas antes de generar el informe.',
                'Sin Metas'
            );
            return;
        }

        // Establecer fechas por defecto (fechas del plan)
        this.fechaInicioInforme = plan.fecha_inicio || new Date(plan.anio, 0, 1).toISOString().split('T')[0];
        this.fechaFinInforme = plan.fecha_fin || new Date(plan.anio, 11, 31).toISOString().split('T')[0];
        this.planParaInforme = plan;
        this.mostrarSelectorFechasInforme = true;
    }

    cancelarInforme(): void {
        this.mostrarSelectorFechasInforme = false;
        this.planParaInforme = null;
    }

    async generarInformePlan(plan?: PlanInstitucional): Promise<void> {
        // Si se llama sin plan, usar el planParaInforme del modal
        const planActual = plan || this.planParaInforme;

        if (!planActual?.id) {
            this.alertService.error('No se puede generar el informe de un plan sin ID', 'Error');
            return;
        }

        // Validar fechas si se está usando el selector
        if (!plan && this.mostrarSelectorFechasInforme) {
            if (!this.fechaInicioInforme || !this.fechaFinInforme) {
                this.alertService.warning('Debes seleccionar el rango de fechas para el informe.', 'Fechas Requeridas');
                return;
            }

            const inicio = new Date(this.fechaInicioInforme + 'T00:00:00');
            const fin = new Date(this.fechaFinInforme + 'T23:59:59');

            if (inicio > fin) {
                this.alertService.warning('La fecha inicial no puede ser posterior a la fecha final.', 'Fechas Inválidas');
                return;
            }
        }

        // Cerrar el selector de fechas si está abierto
        this.mostrarSelectorFechasInforme = false;

        this.generandoInforme = true;

        try {
            // Obtener metas del plan
            const metas = this.getMetasDePlan(planActual.id);

            if (metas.length === 0) {
                this.alertService.warning(
                    'El plan no tiene metas registradas. Agregue metas antes de generar el informe.',
                    'Sin Metas'
                );
                this.generandoInforme = false;
                return;
            }

            // Filtrar metas por rango de fechas si se especificó
            let metasFiltradas = metas;
            if (this.fechaInicioInforme && this.fechaFinInforme) {
                const inicio = new Date(this.fechaInicioInforme);
                const fin = new Date(this.fechaFinInforme);

                metasFiltradas = metas.filter(meta => {
                    const fechaInicio = new Date(meta.fecha_inicio);
                    const fechaFin = new Date(meta.fecha_fin);

                    // Incluir meta si su rango se superpone con el rango del informe
                    return (fechaInicio <= fin && fechaFin >= inicio);
                });

                if (metasFiltradas.length === 0) {
                    this.alertService.warning(
                        'No hay metas en el rango de fechas seleccionado.',
                        'Sin Datos'
                    );
                    this.generandoInforme = false;
                    return;
                }
            }

            this.alertService.info('Generando informe con gráficos y análisis de IA... Por favor espera.', 'Generando Informe');

            // Calcular estadísticas
            const totalMetas = metasFiltradas.length;
            const metasCompletadas = metasFiltradas.filter(m => m.estado === 'completada').length;
            const metasEnProgreso = metasFiltradas.filter(m => m.estado === 'en_progreso').length;
            const metasAtrasadas = metasFiltradas.filter(m => m.estado === 'atrasada').length;
            const metasNoIniciadas = metasFiltradas.filter(m => m.estado === 'no_iniciada').length;

            const avanceGlobal = totalMetas > 0
                ? Math.round(metasFiltradas.reduce((sum, m) => sum + this.getPorcentajeAvance(m), 0) / totalMetas)
                : 0;

            // Capturar gráficos como imágenes (solo si estamos en vista analytics)
            let graficos = null;
            if (this.vistaActual === 'analytics' && this.analyticsData) {
                graficos = await this.capturarGraficos();
            }

            // Preparar datos para análisis AI
            const analysisRequest: PlanAnalysisRequest = {
                planNombre: planActual.nombre,
                planAnio: planActual.anio,
                totalMetas,
                metasCompletadas,
                metasEnProgreso,
                metasAtrasadas,
                metasNoIniciadas,
                avanceGlobal,
                metas: metasFiltradas
            };

            // Generar análisis con IA
            this.aiService.generatePlanAnalysis(analysisRequest).subscribe({
                next: (aiAnalysis) => {
                    // Formatear fechas para el PDF
                    let periodoTexto = `Año ${planActual.anio}`;
                    if (this.fechaInicioInforme && this.fechaFinInforme) {
                        const inicio = new Date(this.fechaInicioInforme);
                        const fin = new Date(this.fechaFinInforme);
                        const opciones: Intl.DateTimeFormatOptions = { year: 'numeric', month: 'long', day: 'numeric' };
                        periodoTexto = `${inicio.toLocaleDateString('es-CO', opciones)} - ${fin.toLocaleDateString('es-CO', opciones)}`;
                    }

                    // Generar PDF
                    this.planReportService.generatePlanPDFReport(
                        planActual,
                        metasFiltradas,
                        aiAnalysis,
                        graficos,
                        periodoTexto
                    );

                    this.alertService.success(
                        'El informe PDF del plan institucional se ha generado exitosamente.',
                        'Informe Generado'
                    );

                    this.generandoInforme = false;
                },
                error: (error) => {
                    console.error('Error al generar análisis:', error);
                    this.alertService.error(
                        'No se pudo generar el análisis del plan. Intente nuevamente.',
                        'Error'
                    );
                    this.generandoInforme = false;
                }
            });

        } catch (error) {
            console.error('Error al generar informe:', error);
            this.alertService.error(
                'Ocurrió un error al generar el informe. Verifique los datos e intente nuevamente.',
                'Error'
            );
            this.generandoInforme = false;
        }
    }

    // Capturar gráficos como imágenes
    private async capturarGraficos(): Promise<{ avanceGlobal: string; distribucion: string } | null> {
        try {
            // Dar un pequeño tiempo para que los SVG se rendericen completamente
            await new Promise(resolve => setTimeout(resolve, 500));

            const avanceGlobalElement = document.querySelector('.card-body svg') as SVGElement;

            if (!avanceGlobalElement) {
                console.warn('No se encontraron gráficos para capturar');
                return null;
            }

            // Capturar el SVG del avance global
            const avanceGlobalData = await this.svgToDataURL(avanceGlobalElement);

            // Capturar la tarjeta completa de distribución (las barras de progreso)
            const distribucionElement = document.querySelector('.card-header + .card-body') as HTMLElement;
            const distribucionData = distribucionElement ? await this.htmlToDataURL(distribucionElement) : '';

            return {
                avanceGlobal: avanceGlobalData,
                distribucion: distribucionData
            };
        } catch (error) {
            console.error('Error capturando gráficos:', error);
            return null;
        }
    }

    // Convertir SVG a DataURL
    private async svgToDataURL(svg: SVGElement): Promise<string> {
        const svgData = new XMLSerializer().serializeToString(svg);
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        const img = new Image();

        canvas.width = 200;
        canvas.height = 200;

        return new Promise((resolve) => {
            img.onload = () => {
                ctx?.drawImage(img, 0, 0);
                resolve(canvas.toDataURL('image/png'));
            };
            img.src = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svgData)));
        });
    }

    // Convertir HTML a DataURL usando html2canvas (simplificado)
    private async htmlToDataURL(element: HTMLElement): Promise<string> {
        // Por ahora retornar string vacío, se puede implementar con html2canvas si es necesario
        return '';
    }

    // Calcular días restantes hasta la fecha fin de una meta
    getDiasRestantesMeta(meta: Meta): number {
        // Si ya está completada, no hay días restantes
        if (meta.estado === 'completada') return 0;

        // Fecha fin de la meta
        const fechaFin = new Date(meta.fecha_fin);

        // Fecha actual (hoy)
        const hoy = new Date();

        // Normalizar a medianoche para comparar solo fechas, no horas
        const fechaFinNormalizada = new Date(fechaFin.getFullYear(), fechaFin.getMonth(), fechaFin.getDate());
        const hoyNormalizado = new Date(hoy.getFullYear(), hoy.getMonth(), hoy.getDate());

        // Calcular diferencia en milisegundos
        const diferenciaMs = fechaFinNormalizada.getTime() - hoyNormalizado.getTime();

        // Convertir a días
        const diasRestantes = Math.ceil(diferenciaMs / (1000 * 60 * 60 * 24));

        // Si el resultado es negativo, significa que ya se venció (retornar 0)
        // Si es positivo, retornar los días que quedan
        return Math.max(0, diasRestantes);
    }

    // Verificar metas próximas a vencer (10 días o menos)
    async verificarMetasProximasVencer(): Promise<void> {
        // Obtener todas las metas de todos los planes
        const todasLasMetas: Meta[] = [];

        this.metasPorPlan.forEach((metas) => {
            todasLasMetas.push(...metas);
        });

        // Filtrar metas que no están completadas y están próximas a vencer
        const metasProximasVencer = todasLasMetas.filter(meta => {
            if (meta.estado === 'completada') return false;
            const diasRestantes = this.getDiasRestantesMeta(meta);
            return diasRestantes <= 10 && diasRestantes >= 0;
        });

        if (metasProximasVencer.length > 0) {
            const mensaje = `Tienes ${metasProximasVencer.length} meta(s) próxima(s) a vencer en los próximos 10 días:\n\n` +
                metasProximasVencer.slice(0, 5).map(m =>
                    `• ${m.nombre} - ${m.responsable} (${this.getDiasRestantesMeta(m)} día(s) restante(s))`
                ).join('\n') +
                (metasProximasVencer.length > 5 ? `\n\n...y ${metasProximasVencer.length - 5} más.` : '');

            await this.alertService.warning(mensaje, 'Metas Próximas a Vencer');
        }
    }
}
