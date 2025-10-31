import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { PdmDataService } from '../pdm-data.service';
import { EntityContextService } from '../../../services/entity-context.service';

interface FileInfo {
    name: string;
    size: number;
    type: string;
    lastModified: Date;
}

@Component({
    selector: 'app-pdm-upload',
    standalone: true,
    imports: [
        CommonModule
    ],
    templateUrl: './pdm-upload.component.html',
    styleUrls: ['./pdm-upload.component.scss']
})
export class PdmUploadComponent implements OnInit {
    cargando = signal(false);
    progreso = signal(0);
    archivoCargado = signal<FileInfo | null>(null);
    archivoSeleccionado: File | null = null;
    dragOver = signal(false);

    // Info del caché
    cacheInfo = signal<{ existe: boolean; fecha?: Date; version?: string }>({ existe: false });
    tieneDatos = signal(false);

    private showToast: (message: string, type: 'success' | 'error' | 'info') => void;

    constructor(
        private pdmDataService: PdmDataService,
        private router: Router,
        private entityContext: EntityContextService
    ) {
        // Toast con Bootstrap
        this.showToast = (message: string, type: 'success' | 'error' | 'info' = 'info') => {
            const toast = document.createElement('div');
            toast.className = `toast align-items-center text-white bg-${type === 'error' ? 'danger' : type === 'success' ? 'success' : 'primary'} border-0`;
            toast.setAttribute('role', 'alert');
            toast.innerHTML = `
                <div class="d-flex">
                    <div class="toast-body">${message}</div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            `;

            const container = document.getElementById('toast-container') || (() => {
                const c = document.createElement('div');
                c.id = 'toast-container';
                c.className = 'toast-container position-fixed top-0 end-0 p-3';
                c.style.zIndex = '9999';
                document.body.appendChild(c);
                return c;
            })();

            container.appendChild(toast);
            const bsToast = new (window as any).bootstrap.Toast(toast);
            bsToast.show();
            toast.addEventListener('hidden.bs.toast', () => toast.remove());
        };
    }

    ngOnInit(): void {
        this.verificarCache();
    }

    verificarCache(): void {
        this.cacheInfo.set(this.pdmDataService.obtenerInfoCache());
        this.tieneDatos.set(this.pdmDataService.tieneDatosEnCache());
    }

    onDragOver(event: DragEvent): void {
        event.preventDefault();
        event.stopPropagation();
        this.dragOver.set(true);
    }

    onDragLeave(event: DragEvent): void {
        event.preventDefault();
        event.stopPropagation();
        this.dragOver.set(false);
    }

    onDrop(event: DragEvent): void {
        event.preventDefault();
        event.stopPropagation();
        this.dragOver.set(false);

        const files = event.dataTransfer?.files;
        if (files && files.length > 0) {
            this.seleccionarArchivo(files[0]);
        }
    }

    onFileSelected(event: Event): void {
        const input = event.target as HTMLInputElement;
        if (input.files && input.files.length > 0) {
            this.seleccionarArchivo(input.files[0]);
        }
    }

    seleccionarArchivo(file: File): void {
        // Validar extensión
        const validTypes = [
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.ms-excel'
        ];

        if (!validTypes.includes(file.type)) {
            this.showToast('Por favor selecciona un archivo Excel válido (.xlsx, .xls)', 'error');
            return;
        }

        // Validar tamaño (máximo 10MB)
        const maxSize = 10 * 1024 * 1024;
        if (file.size > maxSize) {
            this.showToast('El archivo es demasiado grande. Máximo 10MB.', 'error');
            return;
        }

        this.archivoSeleccionado = file;
        this.archivoCargado.set({
            name: file.name,
            size: file.size,
            type: file.type,
            lastModified: new Date(file.lastModified)
        });
    }

    procesarArchivo(): void {
        if (!this.archivoSeleccionado) {
            this.showToast('Por favor selecciona un archivo primero', 'error');
            return;
        }

        this.cargando.set(true);
        this.progreso.set(10);

        // Simular progreso
        const interval = setInterval(() => {
            const currentProgress = this.progreso();
            if (currentProgress < 90) {
                this.progreso.set(currentProgress + 10);
            }
        }, 300);

        this.pdmDataService.procesarArchivoExcel(this.archivoSeleccionado)
            .then(() => {
                clearInterval(interval);
                this.progreso.set(100);

                this.showToast('✅ Excel procesado correctamente. Datos guardados en caché.', 'success');

                // Actualizar info de caché
                this.verificarCache();

                // Navegar al dashboard
                setTimeout(() => {
                    const slug = this.entityContext.currentEntity?.slug || 'default';
                    this.router.navigate([`/${slug}/pdm-dashboard`]);
                }, 1500);
            })
            .catch((error) => {
                clearInterval(interval);
                console.error('Error al procesar archivo:', error);

                this.showToast(
                    '❌ Error al procesar el archivo. Verifica que contenga todas las hojas requeridas.',
                    'error'
                );
            })
            .finally(() => {
                this.cargando.set(false);
                this.progreso.set(0);
            });
    }

    irAlDashboard(): void {
        const slug = this.entityContext.currentEntity?.slug || 'default';
        this.router.navigate([`/${slug}/pdm-dashboard`]);
    }

    limpiarDatos(): void {
        if (confirm('¿Estás seguro de eliminar los datos almacenados? Deberás cargar el Excel nuevamente.')) {
            this.pdmDataService.limpiarDatos();
            this.archivoCargado.set(null);
            this.archivoSeleccionado = null;
            this.verificarCache();

            this.showToast('Datos eliminados correctamente', 'success');
        }
    }

    formatBytes(bytes: number): string {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
    }

    formatDate(date: Date): string {
        return new Intl.DateTimeFormat('es-ES', {
            day: '2-digit',
            month: 'short',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        }).format(date);
    }
}
