import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

export interface AvanceDialogData {
    codigo: string;
    avances?: { [anio: number]: { valor: number; comentario?: string } };
    programacion?: { [anio: number]: number };
}

@Component({
    selector: 'app-pdm-avance-dialog',
    standalone: true,
    imports: [
        CommonModule,
        FormsModule
    ],
    templateUrl: './pdm-avance-dialog.component.html',
    styleUrls: ['./pdm-avance-dialog.component.scss']
})
export class PdmAvanceDialogComponent implements OnInit {
    @Input() data!: AvanceDialogData;
    @Output() onSave = new EventEmitter<{ anio: number; valor_ejecutado: number; comentario: string }>();
    @Output() onCancel = new EventEmitter<void>();

    anios = [2024, 2025, 2026, 2027];
    anio: number = new Date().getFullYear() > 2027 ? 2027 : (new Date().getFullYear() < 2024 ? 2024 : new Date().getFullYear());
    valor_ejecutado: number = 0; // incremento a registrar en este avance
    comentario: string = '';
    error: string | null = null;

    get metaAnio(): number {
        return this.data?.programacion?.[this.anio] ?? 0;
    }

    get ejecutadoActual(): number {
        return this.data?.avances?.[this.anio]?.valor ?? 0;
    }

    get maxPermitido(): number {
        // Nunca exceder meta del año ni 100 en caso de que la meta sea >100
        const tope = Math.min(this.metaAnio || 0, 100);
        const restante = Math.max(0, tope - (this.ejecutadoActual || 0));
        return restante;
    }

    constructor() { }

    ngOnInit(): void {
        // Forzar el año actual y preparar datos iniciales
        this.anio = this.anio; // ya inicializado al año en curso dentro del rango
        this.preloadFromData();
    }

    preloadFromData(): void {
        if (this.data.avances && this.data.avances[this.anio]) {
            const a = this.data.avances[this.anio];
            this.valor_ejecutado = a.valor ?? 0;
            this.comentario = a.comentario ?? '';
        }
    }

    onAnioChange(): void {
        // Al cambiar de año, precargar valores existentes si los hay
        this.error = null;
        this.valor_ejecutado = 0;
        this.comentario = '';
        this.preloadFromData();
    }

    guardar() {
        this.error = null;
        if (!this.anio) {
            this.error = 'Selecciona un año válido.';
            return;
        }
        if (this.maxPermitido <= 0) {
            this.error = 'La meta del año ya está completamente ejecutada.';
            return;
        }
        if (this.valor_ejecutado < 1 || this.valor_ejecutado > this.maxPermitido) {
            this.error = `El valor debe estar entre 1 y ${this.maxPermitido} (restante del año).`;
            return;
        }
        this.onSave.emit({ anio: this.anio, valor_ejecutado: this.valor_ejecutado, comentario: this.comentario });
    }

    cancelar() {
        this.onCancel.emit();
    }
}
