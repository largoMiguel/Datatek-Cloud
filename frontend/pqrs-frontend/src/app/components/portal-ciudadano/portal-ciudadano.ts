import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { PqrsService } from '../../services/pqrs.service';
import { AlertService } from '../../services/alert.service';
import { User } from '../../models/user.model';
import { PQRSWithDetails } from '../../models/pqrs.model';

@Component({
    selector: 'app-portal-ciudadano',
    standalone: true,
    imports: [CommonModule, FormsModule, ReactiveFormsModule],
    templateUrl: './portal-ciudadano.html',
    styleUrl: './portal-ciudadano.scss'
})
export class PortalCiudadanoComponent implements OnInit {
    // Estados de vista
    isLoggedIn = false;
    showRegisterForm = false;

    // Usuario actual
    currentUser: User | null = null;

    // Formularios
    loginForm: FormGroup;
    registerForm: FormGroup;

    // Estados
    isLoading = false;
    isSubmitting = false;

    // PQRS del ciudadano
    misPqrs: PQRSWithDetails[] = [];
    selectedPqrs: PQRSWithDetails | null = null;
    showDetails = false;

    constructor(
        private authService: AuthService,
        private pqrsService: PqrsService,
        private router: Router,
        private fb: FormBuilder,
        private alertService: AlertService
    ) {
        this.loginForm = this.fb.group({
            username: ['', Validators.required],
            password: ['', Validators.required]
        });

        this.registerForm = this.fb.group({
            username: ['', Validators.required],
            password: ['', [Validators.required, Validators.minLength(6)]],
            password_confirm: ['', Validators.required],
            full_name: ['', Validators.required],
            email: ['', [Validators.required, Validators.email]],
            cedula: ['', Validators.required],
            telefono: [''],
            direccion: ['']
        }, { validators: this.passwordMatchValidator });
    }

    ngOnInit() {
        // Verificar si ya está autenticado
        this.authService.getCurrentUser().subscribe({
            next: (user) => {
                if (user && user.role === 'ciudadano') {
                    this.currentUser = user;
                    this.isLoggedIn = true;
                    this.loadMisPqrs();
                }
            },
            error: () => {
                this.isLoggedIn = false;
            }
        });
    }

    passwordMatchValidator(form: FormGroup) {
        const password = form.get('password');
        const confirmPassword = form.get('password_confirm');
        return password && confirmPassword && password.value === confirmPassword.value
            ? null
            : { passwordMismatch: true };
    }

    onLoginSubmit() {
        if (this.loginForm.valid && !this.isSubmitting) {
            this.isSubmitting = true;

            this.authService.login(this.loginForm.value).subscribe({
                next: (response) => {
                    // Verificar que sea un usuario ciudadano
                    this.authService.getCurrentUser().subscribe({
                        next: (user) => {
                            if (user && user.role === 'ciudadano') {
                                this.currentUser = user;
                                this.isLoggedIn = true;
                                this.alertService.success(`Bienvenido ${user.full_name}`, 'Acceso Exitoso');
                                this.loadMisPqrs();
                            } else {
                                this.alertService.warning('Este portal es solo para ciudadanos. Por favor usa el Portal Administrativo.', 'Acceso Restringido');
                                this.authService.logout();
                            }
                            this.isSubmitting = false;
                        }
                    });
                },
                error: (error) => {
                    console.error('Error en login:', error);
                    this.alertService.error('Usuario o contraseña incorrectos', 'Error de Acceso');
                    this.isSubmitting = false;
                }
            });
        }
    }

    onRegisterSubmit() {
        if (this.registerForm.valid && !this.isSubmitting) {
            this.isSubmitting = true;

            const { password_confirm, ...userData } = this.registerForm.value;
            const registerData = {
                ...userData,
                role: 'ciudadano'
            };

            this.authService.registerCiudadano(registerData).subscribe({
                next: (response) => {
                    this.alertService.success('Cuenta creada exitosamente. Ya puedes iniciar sesión.', 'Registro Exitoso');
                    this.showRegisterForm = false;
                    this.registerForm.reset();
                    this.isSubmitting = false;
                },
                error: (error) => {
                    console.error('Error en registro:', error);
                    const errorMessage = error.error?.detail || 'No se pudo crear la cuenta. Verifica que el usuario y email no existan.';
                    this.alertService.error(errorMessage, 'Error en Registro');
                    this.isSubmitting = false;
                }
            });
        }
    }

    loadMisPqrs() {
        this.isLoading = true;
        this.pqrsService.getPqrs().subscribe({
            next: (pqrsList) => {
                // Filtrar solo las PQRS del ciudadano actual por cédula o email
                this.misPqrs = pqrsList.filter(pqrs =>
                    pqrs.cedula_ciudadano === this.currentUser?.cedula ||
                    pqrs.email_ciudadano === this.currentUser?.email
                );
                this.isLoading = false;
            },
            error: (error) => {
                console.error('Error cargando PQRS:', error);
                this.isLoading = false;
            }
        });
    }

    verDetalles(pqrs: PQRSWithDetails) {
        this.selectedPqrs = pqrs;
        this.showDetails = true;
    }

    cerrarDetalles() {
        this.selectedPqrs = null;
        this.showDetails = false;
    }

    toggleView() {
        this.showRegisterForm = !this.showRegisterForm;
    }

    logout() {
        this.authService.logout();
        this.isLoggedIn = false;
        this.currentUser = null;
        this.misPqrs = [];
        this.router.navigate(['/']);
    }

    volverAInicio() {
        this.router.navigate(['/']);
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

    getEstadoColor(estado: string): string {
        const colores: { [key: string]: string } = {
            'pendiente': 'warning',
            'en_proceso': 'info',
            'resuelto': 'success',
            'respondido': 'primary',
            'cerrado': 'dark'
        };
        return colores[estado] || 'secondary';
    }

    // Getters para estadísticas (evitan usar filter en la plantilla)
    get totalPqrs(): number {
        return this.misPqrs.length;
    }

    get pqrsEnProceso(): number {
        return this.misPqrs.filter(p => p.estado === 'pendiente' || p.estado === 'en_proceso').length;
    }

    get pqrsResueltas(): number {
        return this.misPqrs.filter(p => p.estado === 'resuelto' || p.estado === 'cerrado').length;
    }
}
