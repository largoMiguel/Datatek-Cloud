import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

export interface AvanceDialogData {
    codigo: string;
    avances?: { [anio: number]: { valor: number; comentario?: string } };
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
    valor_ejecutado: number = 0;
    comentario: string = '';
    error: string | null = null;

    constructor() { }

    ngOnInit(): void {
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
        if (this.valor_ejecutado < 0 || this.valor_ejecutado > 100) {
            this.error = 'El valor debe estar entre 0 y 100%';
            return;
        }
        this.onSave.emit({ anio: this.anio, valor_ejecutado: this.valor_ejecutado, comentario: this.comentario });
    }

    cancelar() {
        this.onCancel.emit();
    }
}
