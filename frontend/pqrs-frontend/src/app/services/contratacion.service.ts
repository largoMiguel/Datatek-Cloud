import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, map, of } from 'rxjs';
import { ProcesoContratacion, FiltroContratacion } from '../models/contratacion.model';
import { environment } from '../../environments/environment';

@Injectable({ providedIn: 'root' })
export class ContratacionService {
    // Proxy en backend para evitar CORS
    private proxyUrl = `${environment.apiUrl}/contratacion/proxy`;
    private cache = new Map<string, { ts: number; data: ProcesoContratacion[] }>();
    private TTL_MS = 5 * 60 * 1000; // 5 minutos

    constructor(private http: HttpClient) { }

    /**
     * Construye la consulta SODA con parámetros usando NIT de la entidad.
     * El campo en SECOP es 'nit_entidad'.
     */
    buildQuery(f: FiltroContratacion): string {
        const condiciones: string[] = [];

        // Filtro principal: NIT de la entidad
        // Si no hay NIT en el filtro, usamos uno de ejemplo (MUNICIPIO DE MOTAVITA)
        const nit = f.entidad?.trim() || '891801994'; // NIT de ejemplo
        condiciones.push(`\`nit_entidad\` = \"${nit.replaceAll('"', '\\"')}\"`);

        // Fechas
        if (f.fechaDesde) {
            condiciones.push(`(\`fecha_de_publicacion_del\` > \"${f.fechaDesde}T00:00:00\" :: floating_timestamp)`);
        }
        if (f.fechaHasta) {
            condiciones.push(`(\`fecha_de_publicacion_del\` <= \"${f.fechaHasta}T23:59:59\" :: floating_timestamp)`);
        }

        // Modalidad, tipo, estado
        if (f.modalidad) condiciones.push(`\`modalidad_de_contratacion\` = \"${f.modalidad.replaceAll('"', '\\"')}\"`);
        if (f.tipoContrato) condiciones.push(`\`tipo_de_contrato\` = \"${f.tipoContrato.replaceAll('"', '\\"')}\"`);
        if (f.estado) condiciones.push(`\`estado_resumen\` = \"${f.estado.replaceAll('"', '\\"')}\"`);

        if (f.adjudicado === 'SI') condiciones.push(`upper(\`adjudicado\`) = \"SI\"`);
        if (f.adjudicado === 'NO') condiciones.push(`upper(\`adjudicado\`) = \"NO\"`);

        // Rango de precio base
        if (typeof f.precioMin === 'number') {
            condiciones.push(`to_number(\`precio_base\`) >= ${f.precioMin}`);
        }
        if (typeof f.precioMax === 'number') {
            condiciones.push(`to_number(\`precio_base\`) <= ${f.precioMax}`);
        }

        // Búsqueda textual
        if (f.texto && f.texto.trim().length > 0) {
            const t = f.texto.trim().replaceAll('"', '\\"');
            condiciones.push(`(upper(\`descripci_n_del_procedimiento\`) like upper(\"%${t}%\") OR upper(\`referencia_del_proceso\`) like upper(\"%${t}%\"))`);
        }

        const where = condiciones.length ? `WHERE\n  ${condiciones.join('\n  AND ')}` : '';

        const select = [
            '\n  \`referencia_del_proceso\`',
            '  \`fase\`',
            '  \`fecha_de_publicacion_del\`',
            '  \`fecha_de_ultima_publicaci\`',
            '  \`precio_base\`',
            '  \`modalidad_de_contratacion\`',
            '  \`duracion\`',
            '  \`unidad_de_duracion\`',
            '  \`fecha_de_recepcion_de\`',
            '  \`fecha_de_apertura_efectiva\`',
            '  \`adjudicado\`',
            '  \`fecha_adjudicacion\`',
            '  \`valor_total_adjudicacion\`',
            '  \`nombre_del_proveedor\`',
            '  \`estado_de_apertura_del_proceso\`',
            '  \`estado_resumen\`',
            '  \`urlproceso\`',
            '  \`descripci_n_del_procedimiento\`',
            '  \`tipo_de_contrato\`'
        ].join(',\n');

        const order = 'ORDER BY \`referencia_del_proceso\` ASC NULL LAST';

        const query = `SELECT${select}\n${where}\n${order}`;
        return query;
    }

    fetchProcesos(filtro: FiltroContratacion, forceRefresh = false): Observable<ProcesoContratacion[]> {
        const query = this.buildQuery(filtro);
        const cacheKey = query;
        const now = Date.now();

        if (!forceRefresh && this.cache.has(cacheKey)) {
            const entry = this.cache.get(cacheKey)!;
            if (now - entry.ts < this.TTL_MS) {
                return of(entry.data);
            }
        }

        const params = new HttpParams().set('$query', query);
        return this.http.get<ProcesoContratacion[]>(this.proxyUrl, { params }).pipe(
            map(rows => {
                const data = rows || [];
                this.cache.set(cacheKey, { ts: now, data });
                return data;
            })
        );
    }
}
