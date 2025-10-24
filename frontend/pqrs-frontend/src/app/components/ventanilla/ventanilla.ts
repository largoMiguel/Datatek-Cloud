import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { PqrsService } from '../../services/pqrs.service';
import { AlertService } from '../../services/alert.service';

@Component({
    selector: 'app-ventanilla',
    standalone: true,
    imports: [CommonModule, FormsModule],
    templateUrl: './ventanilla.html',
    styleUrl: './ventanilla.scss'
})
export class VentanillaComponent {
    // Modal states
    mostrarModalRadicacion = false;
    mostrarModalConsulta = false;
    mostrarResultadoConsulta = false;

    // Formulario de radicación
    radicacionForm = {
        tipo_solicitud: '',
        cedula_ciudadano: '',
        nombre_ciudadano: '',
        telefono_ciudadano: '',
        email_ciudadano: '',
        direccion_ciudadano: '',
        asunto: '',
        descripcion: ''
    };

    // Consulta
    numeroRadicado = '';
    pqrsConsultada: any = null;
    isSubmitting = false;
    isConsulting = false;

    constructor(
        private router: Router,
        private pqrsService: PqrsService,
        private alertService: AlertService
    ) { }

    navigateToLogin() {
        this.router.navigate(['/login']);
    }

    navigateToPortalCiudadano() {
        this.router.navigate(['/portal-ciudadano']);
    }

    navigateToConsulta() {
        this.mostrarModalConsulta = true;
    }

    navigateToRadicacion() {
        this.mostrarModalRadicacion = true;
    }

    cerrarModalRadicacion() {
        this.mostrarModalRadicacion = false;
        this.resetFormularioRadicacion();
    }

    cerrarModalConsulta() {
        this.mostrarModalConsulta = false;
        this.numeroRadicado = '';
    }

    cerrarResultadoConsulta() {
        this.mostrarResultadoConsulta = false;
        this.pqrsConsultada = null;
        this.numeroRadicado = '';
    }

    resetFormularioRadicacion() {
        this.radicacionForm = {
            tipo_solicitud: '',
            cedula_ciudadano: '',
            nombre_ciudadano: '',
            telefono_ciudadano: '',
            email_ciudadano: '',
            direccion_ciudadano: '',
            asunto: '',
            descripcion: ''
        };
    }

    generarNumeroRadicado(): string {
        const hoy = new Date();
        const year = hoy.getFullYear();
        const month = String(hoy.getMonth() + 1).padStart(2, '0');
        const day = String(hoy.getDate()).padStart(2, '0');
        const fechaBase = `${year}${month}${day}`;
        const numeroAleatorio = Math.floor(Math.random() * 1000).toString().padStart(3, '0');
        return `${fechaBase}${numeroAleatorio}`;
    }

    submitRadicacion() {
        // Validar campos requeridos
        if (!this.radicacionForm.tipo_solicitud || !this.radicacionForm.cedula_ciudadano ||
            !this.radicacionForm.nombre_ciudadano || !this.radicacionForm.asunto ||
            !this.radicacionForm.descripcion) {
            this.alertService.warning('Por favor completa todos los campos obligatorios marcados con *', 'Campos Requeridos');
            return;
        }

        this.isSubmitting = true;

        const numeroRadicado = this.generarNumeroRadicado();
        const pqrsData: any = {
            ...this.radicacionForm,
            numero_radicado: numeroRadicado
        };

        this.pqrsService.createPqrs(pqrsData).subscribe({
            next: (response) => {
                this.alertService.success(
                    `Tu PQRS ha sido radicada exitosamente.\n\nNúmero de radicado: ${numeroRadicado}\n\nGuarda este número para consultar el estado de tu solicitud.`,
                    'PQRS Radicada'
                );
                this.cerrarModalRadicacion();
                this.isSubmitting = false;
            },
            error: (error) => {
                console.error('Error radicando PQRS:', error);
                this.alertService.error(
                    'No se pudo radicar la PQRS. Por favor, intenta nuevamente o contacta con la administración.',
                    'Error al Radicar'
                );
                this.isSubmitting = false;
            }
        });
    }

    consultarPqrs() {
        if (!this.numeroRadicado.trim()) {
            this.alertService.warning('Por favor ingresa un número de radicado válido.', 'Número Requerido');
            return;
        }

        this.isConsulting = true;

        this.pqrsService.getPqrs().subscribe({
            next: (pqrsList) => {
                const pqrs = pqrsList.find(p => p.numero_radicado === this.numeroRadicado.trim());

                if (pqrs) {
                    this.pqrsConsultada = pqrs;
                    this.mostrarModalConsulta = false;
                    this.mostrarResultadoConsulta = true;
                } else {
                    this.alertService.warning(
                        `No se encontró ninguna PQRS con el número de radicado: ${this.numeroRadicado}.\n\nVerifica el número e intenta nuevamente.`,
                        'PQRS No Encontrada'
                    );
                }
                this.isConsulting = false;
            },
            error: (error) => {
                console.error('Error consultando PQRS:', error);
                this.alertService.error(
                    'No se pudo consultar la PQRS. Por favor, intenta nuevamente más tarde.',
                    'Error en Consulta'
                );
                this.isConsulting = false;
            }
        });
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
}
