import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Actividad } from '../pdm.models';

export interface AvanceDialogData {
    codigo: string;
    avances?: { [anio: number]: { valor: number; comentario?: string } };
    actividades?: Actividad[];
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
    @Output() onSave = new EventEmitter<{ actividadId: number; comentario: string; evidencia?: File | null }>();
    @Output() onCancel = new EventEmitter<void>();

    actividades: Actividad[] = [];
    actividadId: number | null = null;
    comentario: string = '';
    evidencia: File | null = null;
    error: string | null = null;

    constructor() { }

    ngOnInit(): void {
        this.actividades = this.data.actividades || [];
        if (this.actividades.length) {
            this.actividadId = this.actividades[0].id ?? null;
        }
    }

    onActividadChange(): void {
        this.error = null;
    }

    onFileChange(event: Event): void {
        const input = event.target as HTMLInputElement;
        this.evidencia = input.files?.[0] || null;
    }

    guardar() {
        this.error = null;
        if (!this.actividadId) {
            this.error = 'Selecciona una actividad.';
            return;
        }
        this.onSave.emit({ actividadId: this.actividadId, comentario: this.comentario, evidencia: this.evidencia });
    }

    cancelar() {
        this.onCancel.emit();
    }
}
