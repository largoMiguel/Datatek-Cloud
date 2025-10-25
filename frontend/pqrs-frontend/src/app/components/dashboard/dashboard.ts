import { Component, OnInit, OnDestroy, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { PqrsService } from '../../services/pqrs.service';
import { UserService } from '../../services/user.service';
import { AlertService } from '../../services/alert.service';
import { AiService } from '../../services/ai.service';
import { ReportService } from '../../services/report.service';
import { User } from '../../models/user.model';
import { PQRSWithDetails, ESTADOS_PQRS, EstadoPQRS, UpdatePQRSRequest, PQRSResponse, TIPOS_IDENTIFICACION, MEDIOS_RESPUESTA } from '../../models/pqrs.model';
import { BaseChartDirective } from 'ng2-charts';
import { Chart, ChartConfiguration, ChartData, ChartType, registerables } from 'chart.js';

// Registrar todos los componentes de Chart.js
Chart.register(...registerables);

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, FormsModule, ReactiveFormsModule, BaseChartDirective, RouterLink],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.scss'
})
export class DashboardComponent implements OnInit, OnDestroy {
  @ViewChild(BaseChartDirective) chart?: BaseChartDirective;

  currentUser: User | null = null;
  pqrsList: PQRSWithDetails[] = [];
  usuariosList: User[] = [];
  secretariosList: User[] = [];
  isLoading = true;
  isLoadingUsuarios = false;
  isSubmitting = false;
  estadosColor = ESTADOS_PQRS;
  tiposIdentificacion = TIPOS_IDENTIFICACION;
  mediosRespuesta = MEDIOS_RESPUESTA;
  activeView = 'dashboard';
  nuevaPqrsForm: FormGroup;
  nuevoSecretarioForm: FormGroup;
  selectedPqrs: PQRSWithDetails | null = null;
  respuestaTexto = '';
  selectedSecretarioId: number | null = null;
  selectedEstado: string = '';

  // Fechas para el informe
  fechaInicio: string = '';
  fechaFin: string = '';
  mostrarSelectorFechas: boolean = false;
  filtroSecretario: string = '';
  filtroEstado: string = '';
  filtroTipo: string = '';

  // Filtros generales para la vista
  filtroGeneralSecretario: string = '';
  filtroGeneralEstado: string = '';
  filtroGeneralTipo: string = '';
  textoBusqueda: string = '';

  // Para edición de PQRS
  mostrarFormularioEdicion: boolean = false;
  pqrsEditando: PQRSWithDetails | null = null;
  editarPqrsForm: FormGroup;

  // Datos para gráficos
  estadosChartData: ChartData<'doughnut'> = { labels: [], datasets: [] };
  tiposChartData: ChartData<'bar'> = { labels: [], datasets: [] };
  tendenciasChartData: ChartData<'line'> = { labels: [], datasets: [] };

  doughnutChartType: ChartType = 'doughnut';
  barChartType: ChartType = 'bar';
  lineChartType: ChartType = 'line';

  chartOptions: ChartConfiguration['options'] = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: 'bottom'
      }
    }
  };

  constructor(
    private authService: AuthService,
    private pqrsService: PqrsService,
    private userService: UserService,
    private router: Router,
    private fb: FormBuilder,
    private alertService: AlertService,
    private aiService: AiService,
    private reportService: ReportService
  ) {
    this.nuevaPqrsForm = this.fb.group({
      tipo_identificacion: ['personal', Validators.required],
      medio_respuesta: ['email', Validators.required],
      tipo_solicitud: ['', Validators.required],
      cedula_ciudadano: [''],
      nombre_ciudadano: [''],
      telefono_ciudadano: [''],
      email_ciudadano: [''],
      direccion_ciudadano: [''],
      asunto: [''],
      descripcion: ['', Validators.required]
    });

    // Escuchar cambios en tipo_identificacion para ajustar validaciones
    this.nuevaPqrsForm.get('tipo_identificacion')?.valueChanges.subscribe(tipo => {
      const cedulaControl = this.nuevaPqrsForm.get('cedula_ciudadano');
      const nombreControl = this.nuevaPqrsForm.get('nombre_ciudadano');
      const asuntoControl = this.nuevaPqrsForm.get('asunto');

      if (tipo === 'personal') {
        // PQRS Personal: cedula, nombre y asunto obligatorios
        cedulaControl?.setValidators([Validators.required]);
        nombreControl?.setValidators([Validators.required]);
        asuntoControl?.setValidators([Validators.required]);
      } else {
        // PQRS Anónima: solo descripción obligatoria
        cedulaControl?.clearValidators();
        nombreControl?.clearValidators();
        asuntoControl?.clearValidators();
      }

      cedulaControl?.updateValueAndValidity();
      nombreControl?.updateValueAndValidity();
      asuntoControl?.updateValueAndValidity();
    });

    // Escuchar cambios en medio_respuesta para ajustar validaciones
    this.nuevaPqrsForm.get('medio_respuesta')?.valueChanges.subscribe(medio => {
      const emailControl = this.nuevaPqrsForm.get('email_ciudadano');
      const direccionControl = this.nuevaPqrsForm.get('direccion_ciudadano');
      const telefonoControl = this.nuevaPqrsForm.get('telefono_ciudadano');

      // Limpiar validaciones primero
      emailControl?.clearValidators();
      direccionControl?.clearValidators();
      telefonoControl?.clearValidators();

      // Agregar validación según el medio seleccionado
      if (medio === 'email') {
        emailControl?.setValidators([Validators.required, Validators.email]);
      } else if (medio === 'fisica') {
        direccionControl?.setValidators([Validators.required]);
      } else if (medio === 'telefono') {
        telefonoControl?.setValidators([Validators.required]);
      }

      emailControl?.updateValueAndValidity();
      direccionControl?.updateValueAndValidity();
      telefonoControl?.updateValueAndValidity();
    });

    this.nuevoSecretarioForm = this.fb.group({
      full_name: ['', Validators.required],
      username: ['', Validators.required],
      email: ['', [Validators.required, Validators.email]],
      secretaria: [''],
      password: ['', [Validators.required, Validators.minLength(6)]],
      password_confirm: ['', Validators.required]
    }, { validators: this.passwordMatchValidator });

    this.editarPqrsForm = this.fb.group({
      tipo_solicitud: ['', Validators.required],
      cedula_ciudadano: ['', Validators.required],
      nombre_ciudadano: ['', Validators.required],
      telefono_ciudadano: [''],
      email_ciudadano: [''],
      direccion_ciudadano: [''],
      asunto: ['', Validators.required],
      descripcion: ['', Validators.required],
      fecha_solicitud: ['', Validators.required]
    });
  }

  // Validador personalizado para confirmar contraseñas
  passwordMatchValidator(form: FormGroup) {
    const password = form.get('password');
    const confirmPassword = form.get('password_confirm');
    return password && confirmPassword && password.value === confirmPassword.value
      ? null
      : { passwordMismatch: true };
  }

  ngOnInit() {
    // Prevenir retroceso al login después de autenticarse
    window.history.pushState(null, '', window.location.href);
    window.onpopstate = () => {
      window.history.pushState(null, '', window.location.href);
    };

    this.authService.getCurrentUser().subscribe({
      next: (user) => {
        this.currentUser = user;
        if (!this.currentUser) {
          this.router.navigate(['/login'], { replaceUrl: true });
          return;
        }
        this.loadPqrs();
        this.loadSecretarios();
      },
      error: () => {
        this.router.navigate(['/login'], { replaceUrl: true });
      }
    });
  }

  ngOnDestroy() {
    // Limpiar el listener de popstate para evitar memory leaks
    window.onpopstate = null;
  }

  setActiveView(view: string) {
    this.activeView = view;
  }

  loadPqrs() {
    this.isLoading = true;
    this.pqrsService.getPqrs().subscribe({
      next: (data) => {
        this.pqrsList = data;
        this.isLoading = false;
        this.updateCharts();
        // Verificar PQRS próximas a vencer
        this.verificarPqrsProximasVencer();
      },
      error: (error) => {
        // console.error('Error cargando PQRS:', error);
        this.isLoading = false;
        if (error.status === 401) {
          this.setActiveView('dashboard');
        }
      }
    });
  }

  loadSecretarios() {
    this.userService.getSecretarios().subscribe({
      next: (data) => {
        this.secretariosList = data;
      },
      error: (error) => {
        // console.error('Error cargando secretarios:', error);
      }
    });
  }

  loadUsuarios() {
    this.isLoadingUsuarios = true;
    this.userService.getUsers().subscribe({
      next: (data) => {
        this.usuariosList = data;
        this.isLoadingUsuarios = false;
      },
      error: (error) => {
        // console.error('Error cargando usuarios:', error);
        this.isLoadingUsuarios = false;
      }
    });
  }

  verDetallesPqrs(pqrs: any) {
    this.selectedPqrs = pqrs;
    this.setActiveView('detalle-pqrs');
  }

  cerrarDetalles() {
    this.selectedPqrs = null;
    this.setActiveView('dashboard');
  }

  getMisPqrs(): PQRSWithDetails[] {
    let pqrsBase: PQRSWithDetails[] = [];

    // Obtener lista base según rol
    if (this.isAdmin()) {
      pqrsBase = this.pqrsList;
    } else if (this.isSecretario() && this.currentUser) {
      pqrsBase = this.pqrsList.filter(pqrs => pqrs.assigned_to_id === this.currentUser!.id);
    }

    // Aplicar filtros generales
    return this.aplicarFiltrosGenerales(pqrsBase);
  }

  // Aplica los filtros generales a una lista de PQRS
  aplicarFiltrosGenerales(pqrsList: PQRSWithDetails[]): PQRSWithDetails[] {
    let resultado = [...pqrsList];

    // Filtro por secretario
    if (this.filtroGeneralSecretario) {
      resultado = resultado.filter(pqrs =>
        pqrs.assigned_to_id?.toString() === this.filtroGeneralSecretario
      );
    }

    // Filtro por estado
    if (this.filtroGeneralEstado) {
      resultado = resultado.filter(pqrs => pqrs.estado === this.filtroGeneralEstado);
    }

    // Filtro por tipo
    if (this.filtroGeneralTipo) {
      resultado = resultado.filter(pqrs => pqrs.tipo_solicitud === this.filtroGeneralTipo);
    }

    // Filtro por texto de búsqueda
    if (this.textoBusqueda.trim()) {
      const busqueda = this.textoBusqueda.toLowerCase().trim();
      resultado = resultado.filter(pqrs =>
        pqrs.numero_radicado.toLowerCase().includes(busqueda) ||
        (pqrs.nombre_ciudadano || '').toLowerCase().includes(busqueda) ||
        (pqrs.asunto || '').toLowerCase().includes(busqueda) ||
        pqrs.descripcion.toLowerCase().includes(busqueda) ||
        (pqrs.cedula_ciudadano || '').includes(busqueda)
      );
    }

    return resultado;
  }

  // Limpiar filtros generales
  limpiarFiltrosGenerales(): void {
    this.filtroGeneralSecretario = '';
    this.filtroGeneralEstado = '';
    this.filtroGeneralTipo = '';
    this.textoBusqueda = '';
  }

  // Filtrar por estado desde las tarjetas de estadísticas y navegar a Mis PQRS
  filtrarPorEstado(estado: string): void {
    // Limpiar filtros previos
    this.limpiarFiltrosGenerales();

    // Aplicar el nuevo filtro de estado (string vacío = todos)
    if (estado) {
      this.filtroGeneralEstado = estado;
    }

    // Cambiar a la vista de Mis PQRS
    this.setActiveView('mis-pqrs');
  }

  mostrarAsignacion(pqrs: any): void {
    this.selectedPqrs = pqrs;
    this.selectedSecretarioId = pqrs.assigned_to_id || null;
    // Recargar secretarios para asegurar que la lista esté actualizada
    this.loadSecretarios();
  }

  mostrarCambioEstado(pqrs: any): void {
    this.selectedPqrs = pqrs;
    this.selectedEstado = pqrs.estado || '';
  }

  confirmarAsignacion(): void {
    if (this.selectedPqrs && this.selectedSecretarioId) {
      // Validar que el secretario esté activo
      const secretario = this.secretariosList.find(s => s.id === this.selectedSecretarioId);

      if (secretario && !secretario.is_active) {
        this.alertService.warning(
          `El usuario ${secretario.full_name} está inactivo y no puede recibir asignaciones.\n\nPor favor, selecciona un usuario activo.`,
          'Usuario Inactivo'
        );
        return;
      }

      const updateData: UpdatePQRSRequest = {
        assigned_to_id: this.selectedSecretarioId
      };

      this.pqrsService.updatePqrs(this.selectedPqrs.id, updateData).subscribe({
        next: (response) => {
          // console.log('PQRS asignada exitosamente:', response);
          this.alertService.success(
            `La PQRS N° ${this.selectedPqrs?.numero_radicado} ha sido asignada exitosamente a ${secretario?.full_name || 'el usuario seleccionado'}.`
          );
          this.loadPqrs();

          const closeButton = document.querySelector('#asignacionModal .btn-close') as HTMLElement;
          if (closeButton) {
            closeButton.click();
          }
        },
        error: (error) => {
          // console.error('Error asignando PQRS:', error);
          this.alertService.error(
            error.error?.detail || 'No se pudo completar la asignación. Por favor, intenta nuevamente.',
            'Error al Asignar PQRS'
          );
        }
      });
    }
  }

  confirmarCambioEstado(): void {
    if (this.selectedPqrs && this.selectedEstado) {
      const estadoLabel = this.getEstadoLabel(this.selectedEstado);

      const updateData: UpdatePQRSRequest = {
        estado: this.selectedEstado as EstadoPQRS
      };

      this.pqrsService.updatePqrs(this.selectedPqrs.id, updateData).subscribe({
        next: (response) => {
          // console.log('Estado actualizado exitosamente:', response);
          this.alertService.success(
            `El estado de la PQRS N° ${this.selectedPqrs?.numero_radicado} ha sido cambiado a "${estadoLabel}".`
          );
          this.loadPqrs();

          const closeButton = document.querySelector('#estadoModal .btn-close') as HTMLElement;
          if (closeButton) {
            closeButton.click();
          }
        },
        error: (error) => {
          // console.error('Error actualizando estado:', error);
          this.alertService.error(
            error.error?.detail || 'No se pudo actualizar el estado. Por favor, intenta nuevamente.',
            'Error al Cambiar Estado'
          );
        }
      });
    }
  }

  async eliminarPqrs(pqrs: PQRSWithDetails): Promise<void> {
    const confirmacion = await this.alertService.confirm(
      `¿Está seguro de que desea eliminar esta PQRS?\n\n` +
      `Radicado: ${pqrs.numero_radicado}\n` +
      `Ciudadano: ${pqrs.nombre_ciudadano}\n` +
      `Asunto: ${pqrs.asunto}\n\n` +
      `Esta acción no se puede deshacer.`,
      'Confirmar Eliminación'
    );

    if (confirmacion) {
      this.pqrsService.deletePqrs(pqrs.id).subscribe({
        next: () => {
          // console.log('PQRS eliminada exitosamente');
          this.alertService.success(
            `La PQRS N° ${pqrs.numero_radicado} ha sido eliminada correctamente.`
          );

          // Si estábamos viendo los detalles de esta PQRS, volver al dashboard
          if (this.selectedPqrs?.id === pqrs.id) {
            this.setActiveView('dashboard');
            this.selectedPqrs = null;
          }

          // Recargar la lista de PQRS
          this.loadPqrs();
        },
        error: (error) => {
          // console.error('Error eliminando PQRS:', error);
          this.alertService.error(
            error.error?.detail || 'No se pudo eliminar la PQRS. Por favor, intenta nuevamente.',
            'Error al Eliminar'
          );
        }
      });
    }
  }

  onSubmitNuevaPqrs() {
    if (this.nuevaPqrsForm.valid && !this.isSubmitting) {
      this.isSubmitting = true;

      const formData = this.nuevaPqrsForm.value;

      // Generar número de radicado en formato YYYYMMDDNNN
      const numeroRadicado = this.generarNumeroRadicado();
      formData.numero_radicado = numeroRadicado;

      // Convertir cadenas vacías a null para campos opcionales (evita error de validación de email)
      if (!formData.email_ciudadano || formData.email_ciudadano.trim() === '') {
        formData.email_ciudadano = null;
      }
      if (!formData.telefono_ciudadano || formData.telefono_ciudadano.trim() === '') {
        formData.telefono_ciudadano = null;
      }
      if (!formData.direccion_ciudadano || formData.direccion_ciudadano.trim() === '') {
        formData.direccion_ciudadano = null;
      }
      if (!formData.asunto || formData.asunto.trim() === '') {
        formData.asunto = null;
      }
      if (!formData.nombre_ciudadano || formData.nombre_ciudadano.trim() === '') {
        formData.nombre_ciudadano = null;
      }
      if (!formData.cedula_ciudadano || formData.cedula_ciudadano.trim() === '') {
        formData.cedula_ciudadano = null;
      }

      this.pqrsService.createPqrs(formData).subscribe({
        next: (response) => {
          // console.log('PQRS creada exitosamente:', response);
          this.alertService.success(
            `La PQRS ha sido creada exitosamente con el radicado N° ${numeroRadicado}.\n\nPuedes consultarla en cualquier momento usando este número.`,
            'PQRS Creada'
          );
          this.nuevaPqrsForm.reset();
          this.isSubmitting = false;
          this.setActiveView('dashboard');
          this.loadPqrs();
        },
        error: (error) => {
          // console.error('Error creando PQRS:', error);
          this.alertService.error(
            error.error?.message || 'No se pudo crear la PQRS. Por favor, verifica los datos e intenta nuevamente.',
            'Error al Crear PQRS'
          );
          this.isSubmitting = false;
        }
      });
    }
  }

  // Generar número de radicado con formato YYYYMMDDNNN
  generarNumeroRadicado(): string {
    const hoy = new Date();
    const year = hoy.getFullYear();
    const month = String(hoy.getMonth() + 1).padStart(2, '0');
    const day = String(hoy.getDate()).padStart(2, '0');
    const fechaBase = `${year}${month}${day}`;

    // Contar cuántas PQRS existen hoy
    const pqrsHoy = this.pqrsList.filter(pqrs => {
      if (pqrs.numero_radicado && pqrs.numero_radicado.startsWith(fechaBase)) {
        return true;
      }
      return false;
    });

    // El siguiente número será el total + 1
    const siguienteNumero = pqrsHoy.length + 1;
    const numeroSecuencial = String(siguienteNumero).padStart(3, '0');

    return `${fechaBase}${numeroSecuencial}`;
  }

  // Mostrar formulario de edición
  mostrarEdicionPqrs(pqrs: PQRSWithDetails): void {
    this.pqrsEditando = pqrs;

    // Convertir la fecha al formato requerido por input datetime-local (YYYY-MM-DDTHH:MM)
    const fechaSolicitud = new Date(pqrs.fecha_solicitud);
    const fechaFormatted = fechaSolicitud.toISOString().slice(0, 16);

    this.editarPqrsForm.patchValue({
      tipo_solicitud: pqrs.tipo_solicitud,
      cedula_ciudadano: pqrs.cedula_ciudadano,
      nombre_ciudadano: pqrs.nombre_ciudadano,
      telefono_ciudadano: pqrs.telefono_ciudadano || '',
      email_ciudadano: pqrs.email_ciudadano || '',
      direccion_ciudadano: pqrs.direccion_ciudadano || '',
      asunto: pqrs.asunto,
      descripcion: pqrs.descripcion,
      fecha_solicitud: fechaFormatted
    });
    this.mostrarFormularioEdicion = true;
  }

  // Cancelar edición
  cancelarEdicion(): void {
    this.mostrarFormularioEdicion = false;
    this.pqrsEditando = null;
    this.editarPqrsForm.reset();
  }

  // Guardar cambios de edición
  guardarEdicion(): void {
    if (this.editarPqrsForm.valid && this.pqrsEditando && !this.isSubmitting) {
      this.isSubmitting = true;

      const formValue = this.editarPqrsForm.value;

      // Convertir la fecha al formato ISO si fue modificada
      const updateData: UpdatePQRSRequest = {
        ...formValue,
        fecha_solicitud: formValue.fecha_solicitud ? new Date(formValue.fecha_solicitud).toISOString() : undefined
      };

      this.pqrsService.updatePqrs(this.pqrsEditando.id, updateData).subscribe({
        next: () => {
          this.alertService.success('La PQRS ha sido actualizada exitosamente.', 'PQRS Actualizada');
          this.cancelarEdicion();
          this.loadPqrs();
          this.isSubmitting = false;
        },
        error: (error) => {
          // console.error('Error actualizando PQRS:', error);
          this.alertService.error(
            error.error?.message || 'No se pudo actualizar la PQRS. Por favor, intenta nuevamente.',
            'Error al Actualizar'
          );
          this.isSubmitting = false;
        }
      });
    }
  }

  onSubmitNuevoSecretario() {
    if (this.nuevoSecretarioForm.valid && !this.isSubmitting) {
      this.isSubmitting = true;

      const { password_confirm, ...userData } = this.nuevoSecretarioForm.value;

      // Agregar el rol de secretario
      const createData = {
        ...userData,
        role: 'secretario'
      };

      this.userService.createUser(createData).subscribe({
        next: (response) => {
          // console.log('Secretario creado exitosamente:', response);
          this.alertService.success(
            `El secretario ${userData.full_name} ha sido creado exitosamente.\n\nUsuario: ${userData.username}\nEstá activo y listo para recibir asignaciones.`,
            'Secretario Creado'
          );
          this.nuevoSecretarioForm.reset();
          this.isSubmitting = false;
          this.setActiveView('usuarios');
          this.loadUsuarios();
        },
        error: (error) => {
          // console.error('Error creando secretario:', error);
          this.alertService.error(
            error.error?.message || 'No se pudo crear el secretario. Verifica que el usuario y email no existan.',
            'Error al Crear Secretario'
          );
          this.isSubmitting = false;
        }
      });
    }
  }

  enviarRespuesta() {
    if (this.selectedPqrs && this.respuestaTexto.trim()) {
      const updateData: UpdatePQRSRequest = {
        respuesta: this.respuestaTexto.trim(),
        estado: 'resuelto' as EstadoPQRS
      };

      this.pqrsService.updatePqrs(this.selectedPqrs.id, updateData).subscribe({
        next: (response) => {
          // console.log('Respuesta enviada exitosamente:', response);
          // Actualizar el selectedPqrs con la respuesta
          if (this.selectedPqrs) {
            this.selectedPqrs.respuesta = this.respuestaTexto.trim();
            this.selectedPqrs.estado = 'resuelto';
          }
          this.alertService.success(
            `La respuesta ha sido enviada exitosamente y el estado de la PQRS N° ${this.selectedPqrs?.numero_radicado} ha cambiado a "Resuelto".`,
            'Respuesta Enviada'
          );
          this.respuestaTexto = '';
          this.loadPqrs();
        },
        error: (error) => {
          // console.error('Error enviando respuesta:', error);
          this.alertService.error(
            'No se pudo enviar la respuesta. Por favor, verifica tu conexión e intenta nuevamente.',
            'Error al Enviar Respuesta'
          );
        }
      });
    }
  }

  isAdmin(): boolean {
    return this.currentUser?.role === 'admin';
  }

  isSecretario(): boolean {
    return this.currentUser?.role === 'secretario';
  }

  canChangeStatus(): boolean {
    return this.isAdmin() || this.isSecretario();
  }

  canEditPqrs(pqrs: PQRSWithDetails): boolean {
    // Admin puede editar todas
    if (this.isAdmin()) return true;

    // Secretario solo puede editar las que tiene asignadas
    if (this.isSecretario() && this.currentUser) {
      return pqrs.assigned_to_id === this.currentUser.id;
    }

    return false;
  }

  getEstadoColor(estado: string): string {
    const estadosColorMap: { [key: string]: string } = {
      'pendiente': 'warning',
      'en_proceso': 'info',
      'resuelto': 'success',
      'respondido': 'primary',
      'cerrado': 'dark'
    };
    return estadosColorMap[estado] || 'secondary';
  }

  getEstadoLabel(estado: string): string {
    const labels: { [key: string]: string } = {
      'pendiente': 'Pendiente',
      'en_proceso': 'En Proceso',
      'resuelto': 'Resuelto',
      'respondido': 'Respondido',
      'cerrado': 'Cerrado'
    };
    return labels[estado] || estado;
  }

  toggleUsuarioEstado(usuario: User): void {
    // No permitir que el usuario se desactive a sí mismo
    if (usuario.id === this.currentUser?.id) {
      // console.warn('No se puede cambiar el estado del usuario actual.');
      return;
    }

    // Llamar al servicio para alternar el estado
    this.userService.toggleUserStatus(usuario.id).subscribe({
      next: (updatedUser) => {
        // Actualizar la lista de usuarios en memoria
        this.usuariosList = this.usuariosList.map(u => u.id === updatedUser.id ? updatedUser : u);

        // Si el usuario es secretario, actualizar también la lista de secretarios
        if (updatedUser.role === 'secretario') {
          const exists = this.secretariosList.some(s => s.id === updatedUser.id);
          if (updatedUser.is_active && !exists) {
            this.secretariosList = [...this.secretariosList, updatedUser];
          } else if (!updatedUser.is_active && exists) {
            this.secretariosList = this.secretariosList.filter(s => s.id !== updatedUser.id);
          } else {
            this.secretariosList = this.secretariosList.map(s => s.id === updatedUser.id ? updatedUser : s);
          }
        }

        // console.log('Estado de usuario actualizado:', updatedUser);
      },
      error: (error) => {
        // console.error('Error alternando estado de usuario:', error);
      }
    });
  }

  async eliminarUsuario(usuario: User): Promise<void> {
    // No permitir que el usuario se elimine a sí mismo
    if (usuario.id === this.currentUser?.id) {
      this.alertService.warning(
        'No puedes eliminar tu propia cuenta de usuario.\n\nSi necesitas eliminar esta cuenta, solicita a otro administrador que lo haga.',
        'Acción No Permitida'
      );
      return;
    }

    const confirmacion = await this.alertService.confirm(
      `¿Está seguro de que desea eliminar este usuario?\n\n` +
      `Nombre: ${usuario.full_name}\n` +
      `Usuario: ${usuario.username}\n` +
      `Rol: ${usuario.role}\n\n` +
      `Esta acción no se puede deshacer y todas las PQRS asignadas a este usuario quedarán sin asignar.`,
      'Confirmar Eliminación'
    );

    if (confirmacion) {
      this.userService.deleteUser(usuario.id).subscribe({
        next: () => {
          // console.log('Usuario eliminado exitosamente');
          this.alertService.success(
            `El usuario ${usuario.full_name} ha sido eliminado correctamente del sistema.`
          );

          // Recargar las listas de usuarios desde el servidor
          this.loadUsuarios();
          this.loadSecretarios();
        },
        error: (error) => {
          // console.error('Error eliminando usuario:', error);
          this.alertService.error(
            error.error?.detail || 'No se pudo eliminar el usuario. Por favor, intenta nuevamente.',
            'Error al Eliminar Usuario'
          );
        }
      });
    }
  }

  // Métodos de estadísticas
  getTotalPqrs(): number {
    return this.pqrsList.length;
  }

  getPqrsPendientes(): number {
    return this.pqrsList.filter(p => p.estado === 'pendiente').length;
  }

  getPqrsEnProceso(): number {
    return this.pqrsList.filter(p => p.estado === 'en_proceso').length;
  }

  getPqrsResueltas(): number {
    return this.pqrsList.filter(p => p.estado === 'resuelto' || p.estado === 'cerrado').length;
  }

  getPqrsDelMes(): number {
    const hoy = new Date();
    const inicioMes = new Date(hoy.getFullYear(), hoy.getMonth(), 1);
    return this.pqrsList.filter(p => {
      const fecha = new Date(p.fecha_solicitud);
      return fecha >= inicioMes;
    }).length;
  }

  getPqrsSinAsignar(): number {
    return this.pqrsList.filter(p => !p.assigned_to_id).length;
  }

  getPromedioRespuesta(): number {
    const respondidas = this.pqrsList.filter(p => p.respuesta && p.fecha_respuesta);
    if (respondidas.length === 0) return 0;

    const tiempos = respondidas.map(p => {
      const inicio = new Date(p.fecha_solicitud);
      const fin = new Date(p.fecha_respuesta!);
      return (fin.getTime() - inicio.getTime()) / (1000 * 60 * 60 * 24); // días
    });

    const promedio = tiempos.reduce((a, b) => a + b, 0) / tiempos.length;
    return Math.round(promedio * 10) / 10;
  }

  getPqrsPorTipo(tipo: string): number {
    return this.pqrsList.filter(p => p.tipo_solicitud === tipo).length;
  }

  // Calcula los días restantes para responder una PQRS (15 días hábiles desde la fecha de solicitud)
  // Calcula los días restantes para responder una PQRS (15 días hábiles desde la fecha de solicitud)
  getDiasRestantes(pqrs: PQRSWithDetails): number {
    // Si ya está resuelta o cerrada, no hay días restantes
    if (pqrs.estado === 'resuelto' || pqrs.estado === 'cerrado') return 0;

    // Fecha de solicitud (inicio del conteo)
    const fechaSolicitud = new Date(pqrs.fecha_solicitud);

    // Fecha actual (hoy)
    const hoy = new Date();

    // Normalizar a medianoche para comparar solo fechas, no horas
    const fechaSolicitudNormalizada = new Date(fechaSolicitud.getFullYear(), fechaSolicitud.getMonth(), fechaSolicitud.getDate());
    const hoyNormalizado = new Date(hoy.getFullYear(), hoy.getMonth(), hoy.getDate());

    // Calcular diferencia en milisegundos
    const diferenciaMs = hoyNormalizado.getTime() - fechaSolicitudNormalizada.getTime();

    // Convertir a días (positivo si hoy es después, negativo si es antes)
    const diasTranscurridos = Math.floor(diferenciaMs / (1000 * 60 * 60 * 24));

    // Calcular días restantes (15 días totales - días que ya pasaron)
    const diasRestantes = 15 - diasTranscurridos;

    // Si el resultado es negativo, significa que ya se venció (retornar 0)
    // Si es positivo, retornar los días que quedan
    return Math.max(0, diasRestantes);
  }

  // Obtiene los días vencidos (cuando ya pasaron los 15 días)
  getDiasVencidos(pqrs: PQRSWithDetails): number {
    if (pqrs.estado === 'resuelto' || pqrs.estado === 'cerrado') return 0;

    const fechaSolicitud = new Date(pqrs.fecha_solicitud);
    const hoy = new Date();

    const fechaSolicitudNormalizada = new Date(fechaSolicitud.getFullYear(), fechaSolicitud.getMonth(), fechaSolicitud.getDate());
    const hoyNormalizado = new Date(hoy.getFullYear(), hoy.getMonth(), hoy.getDate());

    const diferenciaMs = hoyNormalizado.getTime() - fechaSolicitudNormalizada.getTime();
    const diasTranscurridos = Math.floor(diferenciaMs / (1000 * 60 * 60 * 24));

    // Si pasaron más de 15 días, retornar cuántos días de vencimiento lleva
    const diasVencidos = diasTranscurridos - 15;

    return Math.max(0, diasVencidos);
  }

  // Verifica si la PQRS está vencida
  estaVencida(pqrs: PQRSWithDetails): boolean {
    if (pqrs.estado === 'resuelto' || pqrs.estado === 'cerrado') return false;
    return this.getDiasVencidos(pqrs) > 0;
  }  // Obtiene el color según los días restantes
  getColorDiasRestantes(diasRestantes: number): string {
    if (diasRestantes <= 2) return 'text-danger fw-bold';
    if (diasRestantes <= 5) return 'text-warning fw-bold';
    return 'text-success';
  }

  // Verifica PQRS próximas a vencer (5 días o menos)
  async verificarPqrsProximasVencer(): Promise<void> {
    const pqrsProximasVencer = this.pqrsList.filter(pqrs => {
      if (pqrs.estado === 'resuelto' || pqrs.estado === 'cerrado') return false;
      const diasRestantes = this.getDiasRestantes(pqrs);
      return diasRestantes <= 5 && diasRestantes >= 0;
    });

    if (pqrsProximasVencer.length > 0) {
      const mensaje = `Tienes ${pqrsProximasVencer.length} PQRS próximas a vencer en los próximos 5 días:\n\n` +
        pqrsProximasVencer.slice(0, 5).map(p =>
          `• ${p.numero_radicado} - ${p.asunto} (${this.getDiasRestantes(p)} días restantes)`
        ).join('\n') +
        (pqrsProximasVencer.length > 5 ? `\n\n...y ${pqrsProximasVencer.length - 5} más.` : '');

      await this.alertService.warning(mensaje, 'PQRS Próximas a Vencer');
    }
  }

  updateCharts(): void {
    // Gráfico de estados (Doughnut)
    const estadosLabels = ['Pendiente', 'En Proceso', 'Resuelto', 'Cerrado'];
    const estadosData = [
      this.pqrsList.filter(p => p.estado === 'pendiente').length,
      this.pqrsList.filter(p => p.estado === 'en_proceso').length,
      this.pqrsList.filter(p => p.estado === 'resuelto').length,
      this.pqrsList.filter(p => p.estado === 'cerrado').length,
    ];

    this.estadosChartData = {
      labels: estadosLabels,
      datasets: [{
        data: estadosData,
        backgroundColor: [
          '#ffc107',
          '#17a2b8',
          '#28a745',
          '#343a40'
        ],
        hoverBackgroundColor: [
          '#ffca2c',
          '#1fc8e3',
          '#48c774',
          '#495057'
        ]
      }]
    };

    // Gráfico de tipos (Barras)
    const tiposLabels = ['Petición', 'Queja', 'Reclamo', 'Sugerencia'];
    const tiposData = [
      this.getPqrsPorTipo('peticion'),
      this.getPqrsPorTipo('queja'),
      this.getPqrsPorTipo('reclamo'),
      this.getPqrsPorTipo('sugerencia')
    ];

    this.tiposChartData = {
      labels: tiposLabels,
      datasets: [{
        label: 'PQRS por Tipo',
        data: tiposData,
        backgroundColor: [
          'rgba(33, 107, 168, 0.7)',
          'rgba(255, 193, 7, 0.7)',
          'rgba(220, 53, 69, 0.7)',
          'rgba(40, 167, 69, 0.7)'
        ],
        borderColor: [
          'rgba(33, 107, 168, 1)',
          'rgba(255, 193, 7, 1)',
          'rgba(220, 53, 69, 1)',
          'rgba(40, 167, 69, 1)'
        ],
        borderWidth: 2
      }]
    };

    // Gráfico de tendencias (últimos 7 días)
    const ultimos7Dias = Array.from({ length: 7 }, (_, i) => {
      const d = new Date();
      d.setDate(d.getDate() - (6 - i));
      return d;
    });

    const tendenciasLabels = ultimos7Dias.map(d =>
      d.toLocaleDateString('es-ES', { day: '2-digit', month: '2-digit' })
    );

    const tendenciasData = ultimos7Dias.map(dia => {
      return this.pqrsList.filter(p => {
        const fecha = new Date(p.fecha_solicitud);
        return fecha.toDateString() === dia.toDateString();
      }).length;
    });

    this.tendenciasChartData = {
      labels: tendenciasLabels,
      datasets: [{
        label: 'PQRS Recibidas',
        data: tendenciasData,
        borderColor: '#216ba8',
        backgroundColor: 'rgba(33, 107, 168, 0.1)',
        fill: true,
        tension: 0.4,
        pointBackgroundColor: '#216ba8',
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        pointRadius: 5,
        pointHoverRadius: 7
      }]
    };

    // Actualizar el gráfico si existe
    if (this.chart) {
      this.chart.update();
    }
  }

  mostrarFormularioInforme(): void {
    // Establecer fechas por defecto (último mes)
    const fechaFin = new Date();
    const fechaInicio = new Date();
    fechaInicio.setMonth(fechaInicio.getMonth() - 1);

    this.fechaInicio = fechaInicio.toISOString().split('T')[0];
    this.fechaFin = fechaFin.toISOString().split('T')[0];

    // Resetear filtros
    this.filtroSecretario = '';
    this.filtroEstado = '';
    this.filtroTipo = '';

    this.mostrarSelectorFechas = true;
  }

  cancelarInforme(): void {
    this.mostrarSelectorFechas = false;
    this.filtroSecretario = '';
    this.filtroEstado = '';
    this.filtroTipo = '';
  }

  async generarInforme(): Promise<void> {
    if (!this.fechaInicio || !this.fechaFin) {
      this.alertService.warning('Debes seleccionar el rango de fechas para el informe.', 'Fechas Requeridas');
      return;
    }

    // Convertir fechas a formato comparable (solo fecha, sin hora)
    const inicio = new Date(this.fechaInicio + 'T00:00:00');
    const fin = new Date(this.fechaFin + 'T23:59:59');

    if (inicio > fin) {
      this.alertService.warning('La fecha inicial no puede ser posterior a la fecha final.', 'Fechas Inválidas');
      return;
    }

    try {
      // Cerrar el selector de fechas
      this.mostrarSelectorFechas = false;

      this.alertService.info('Generando informe con análisis de IA... Por favor espera.', 'Generando Informe');

      // Filtrar PQRS por rango de fechas y otros criterios
      let pqrsFiltered = this.pqrsList.filter(pqrs => {
        const fechaSolicitud = new Date(pqrs.fecha_solicitud);
        // Normalizar a solo fecha para comparación
        const fechaSolicitudSolo = new Date(fechaSolicitud.getFullYear(), fechaSolicitud.getMonth(), fechaSolicitud.getDate());
        const inicioSolo = new Date(inicio.getFullYear(), inicio.getMonth(), inicio.getDate());
        const finSolo = new Date(fin.getFullYear(), fin.getMonth(), fin.getDate());

        return fechaSolicitudSolo >= inicioSolo && fechaSolicitudSolo <= finSolo;
      });

      // Aplicar filtro de secretario si está seleccionado
      if (this.filtroSecretario) {
        pqrsFiltered = pqrsFiltered.filter(pqrs =>
          pqrs.assigned_to_id?.toString() === this.filtroSecretario
        );
      }

      // Aplicar filtro de estado si está seleccionado
      if (this.filtroEstado) {
        pqrsFiltered = pqrsFiltered.filter(pqrs => pqrs.estado === this.filtroEstado);
      }

      // Aplicar filtro de tipo si está seleccionado
      if (this.filtroTipo) {
        pqrsFiltered = pqrsFiltered.filter(pqrs => pqrs.tipo_solicitud === this.filtroTipo);
      }

      // console.log('Total PQRS:', this.pqrsList.length);
      // console.log('PQRS filtradas:', pqrsFiltered.length);
      // console.log('Rango:', this.fechaInicio, 'a', this.fechaFin);
      if (this.pqrsList.length > 0) {
        // console.log('Primera PQRS fecha:', this.pqrsList[0].fecha_solicitud);
      } if (pqrsFiltered.length === 0) {
        this.alertService.warning('No hay PQRS en el rango de fechas seleccionado.', 'Sin Datos');
        return;
      }

      // Preparar datos para el análisis de IA
      const tiposPqrs: { [key: string]: number } = {};
      pqrsFiltered.forEach(pqrs => {
        tiposPqrs[pqrs.tipo_solicitud] = (tiposPqrs[pqrs.tipo_solicitud] || 0) + 1;
      });

      // Calcular tiempo promedio de respuesta
      const pqrsConRespuesta = pqrsFiltered.filter(p => p.fecha_respuesta);
      let tiempoPromedioRespuesta = 0;

      if (pqrsConRespuesta.length > 0) {
        const tiempoTotal = pqrsConRespuesta.reduce((acc, pqrs) => {
          const fechaSolicitud = new Date(pqrs.fecha_solicitud).getTime();
          const fechaRespuesta = new Date(pqrs.fecha_respuesta!).getTime();
          const dias = (fechaRespuesta - fechaSolicitud) / (1000 * 60 * 60 * 24);
          return acc + dias;
        }, 0);
        tiempoPromedioRespuesta = Math.round(tiempoTotal / pqrsConRespuesta.length);
      }

      const totalPqrs = pqrsFiltered.length;
      const pendientes = pqrsFiltered.filter(p => p.estado === 'pendiente').length;
      const enProceso = pqrsFiltered.filter(p => p.estado === 'en_proceso').length;
      const resueltas = pqrsFiltered.filter(p => p.estado === 'resuelto').length;
      const cerradas = pqrsFiltered.filter(p => p.estado === 'cerrado').length;
      const tasaResolucion = totalPqrs > 0 ? (resueltas + cerradas) / totalPqrs : 0;

      const aiRequest = {
        totalPqrs,
        pendientes,
        enProceso,
        resueltas,
        cerradas,
        tiposPqrs,
        tiempoPromedioRespuesta,
        tasaResolucion,
        tendenciaMensual: [] as any[],
        fechaInicio: this.fechaInicio,
        fechaFin: this.fechaFin
      };

      // Obtener análisis de IA
      const aiAnalysis = await this.aiService.generateReportAnalysis(aiRequest).toPromise();

      // Preparar analytics
      const analytics = {
        totalPqrs,
        pendientes,
        enProceso,
        resueltas,
        cerradas,
        tiposPqrs,
        tasaResolucion: (tasaResolucion * 100).toFixed(1),
        tiempoPromedioRespuesta
      };

      // Capturar gráficos como imágenes
      const charts = await this.captureCharts();

      // Formatear fechas para el PDF
      const fechaInicioFormat = inicio.toLocaleDateString('es-CO', { year: 'numeric', month: 'long', day: 'numeric' });
      const fechaFinFormat = fin.toLocaleDateString('es-CO', { year: 'numeric', month: 'long', day: 'numeric' });

      // Generar PDF del reporte directamente
      this.reportService.generatePDFReport(
        pqrsFiltered,
        charts,
        aiAnalysis,
        analytics,
        fechaInicioFormat,
        fechaFinFormat
      );

      this.alertService.success('El informe PDF ha sido generado y descargado exitosamente.', 'Informe Generado');

    } catch (error) {
      // console.error('Error generando informe:', error);
      this.alertService.error(
        'Ocurrió un error al generar el informe. Por favor, intenta nuevamente.',
        'Error al Generar Informe'
      );
    }
  }

  private async captureCharts(): Promise<{ estados: string; tipos: string; tendencias: string }> {
    const canvas1 = document.getElementById('estadosChart') as HTMLCanvasElement;
    const canvas2 = document.getElementById('tiposChart') as HTMLCanvasElement;
    const canvas3 = document.getElementById('tendenciasChart') as HTMLCanvasElement;

    return {
      estados: canvas1?.toDataURL('image/png') || '',
      tipos: canvas2?.toDataURL('image/png') || '',
      tendencias: canvas3?.toDataURL('image/png') || ''
    };
  }

  private getPeriodoAnalisis(): string {
    if (this.pqrsList.length === 0) return 'Sin datos';

    const fechas = this.pqrsList.map(p => new Date(p.fecha_solicitud).getTime());
    const fechaMin = new Date(Math.min(...fechas));
    const fechaMax = new Date(Math.max(...fechas));

    const opciones: Intl.DateTimeFormatOptions = { year: 'numeric', month: 'long', day: 'numeric' };
    return `${fechaMin.toLocaleDateString('es-CO', opciones)} - ${fechaMax.toLocaleDateString('es-CO', opciones)}`;
  }

  logout() {
    this.authService.logout();
    this.router.navigate(['/login']);
  }
}
