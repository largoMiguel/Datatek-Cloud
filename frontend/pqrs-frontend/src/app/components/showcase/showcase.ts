import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';

interface Feature {
    icon: string;
    title: string;
    description: string;
    color: string;
}

interface Module {
    name: string;
    icon: string;
    description: string;
    features: string[];
    image: string;
    color: string;
}

interface Stat {
    value: string;
    label: string;
    icon: string;
}

interface Testimonial {
    name: string;
    role: string;
    entity: string;
    message: string;
    avatar: string;
}

@Component({
    selector: 'app-showcase',
    standalone: true,
    imports: [CommonModule, RouterModule],
    templateUrl: './showcase.html',
    styleUrls: ['./showcase.scss']
})
export class ShowcaseComponent implements OnInit {
    features: Feature[] = [
        {
            icon: 'fas fa-shield-alt',
            title: 'Seguro y Confiable',
            description: 'Autenticación robusta con JWT, roles de usuario y control de acceso granular. Cumple con estándares de seguridad gubernamental.',
            color: '#216ba8'
        },
        {
            icon: 'fas fa-mobile-alt',
            title: 'Responsivo 100%',
            description: 'Diseño adaptativo que funciona perfectamente en escritorio, tablet y móvil. Acceso desde cualquier dispositivo.',
            color: '#28a745'
        },
        {
            icon: 'fas fa-tachometer-alt',
            title: 'Alto Rendimiento',
            description: 'Arquitectura optimizada con FastAPI y Angular 18. Respuestas rápidas y experiencia de usuario fluida.',
            color: '#ffc107'
        },
        {
            icon: 'fas fa-chart-line',
            title: 'Analytics Avanzado',
            description: 'Dashboards interactivos con gráficas en tiempo real, KPIs y reportes exportables en PDF y CSV.',
            color: '#17a2b8'
        },
        {
            icon: 'fas fa-database',
            title: 'Base de Datos Robusta',
            description: 'PostgreSQL con migraciones automáticas, backup y recuperación. Escalable para miles de registros.',
            color: '#6610f2'
        },
        {
            icon: 'fas fa-cogs',
            title: 'Multi-entidad',
            description: 'Soporta múltiples entidades gubernamentales en una sola instalación. Personalización por entidad.',
            color: '#dc3545'
        }
    ];

    modules: Module[] = [
        {
            name: 'PQRS - Peticiones, Quejas, Reclamos y Sugerencias',
            icon: 'fas fa-inbox',
            description: 'Sistema completo de gestión de peticiones ciudadanas con flujos de trabajo automatizados, asignación inteligente y seguimiento en tiempo real.',
            features: [
                'Portal ciudadano sin autenticación requerida',
                'Ventanilla única para recepción y clasificación',
                'Dashboard ejecutivo con métricas y alertas',
                'Asignación automática por departamento',
                'Notificaciones por correo electrónico',
                'Respuestas con adjuntos y trazabilidad completa',
                'Reportes estadísticos exportables',
                'Búsqueda avanzada y filtros dinámicos'
            ],
            image: 'fas fa-clipboard-list',
            color: '#216ba8'
        },
        {
            name: 'Planes Institucionales',
            icon: 'fas fa-tasks',
            description: 'Gestión estratégica de planes con seguimiento de objetivos, indicadores y cumplimiento. Alineado con normativa gubernamental colombiana.',
            features: [
                'Creación de planes por entidad',
                'Objetivos estratégicos con metas medibles',
                'Indicadores de gestión con fórmulas personalizadas',
                'Seguimiento de avance con línea de tiempo',
                'Alertas de cumplimiento y vencimientos',
                'Visualización con gráficas de progreso',
                'Exportación de informes ejecutivos',
                'Integración con dashboard central'
            ],
            image: 'fas fa-project-diagram',
            color: '#28a745'
        },
        {
            name: 'Contratación Pública - SECOP II',
            icon: 'fas fa-file-contract',
            description: 'Consulta en tiempo real de procesos de contratación desde SECOP II. Análisis inteligente con IA y reportes profesionales.',
            features: [
                'Integración directa con datos.gov.co',
                'Consulta por NIT de la entidad',
                'KPIs de contratación: adjudicados, montos, tasa de éxito',
                'Gráficas interactivas: estados, modalidades, proveedores',
                'Detección automática de contratos vencidos',
                'Exportación CSV y PDF profesional',
                'Resumen ejecutivo con IA (OpenAI)',
                'Filtros avanzados por fecha, modalidad, tipo'
            ],
            image: 'fas fa-handshake',
            color: '#ffc107'
        },
        {
            name: 'Gestión de Usuarios y Roles',
            icon: 'fas fa-users-cog',
            description: 'Control total de usuarios, permisos y accesos. Sistema de roles jerárquicos con administradores, secretarios, contratistas y portal ciudadano.',
            features: [
                'Admin por entidad con gestión local',
                'Secretarios y contratistas con permisos por módulo',
                'Asignación granular de módulos permitidos',
                'Portal ciudadano sin registro necesario',
                'Activación/desactivación de usuarios',
                'Auditoría completa de acciones',
                'Control de acceso por módulos activos',
                'Gestión simplificada de equipos de trabajo'
            ],
            image: 'fas fa-user-shield',
            color: '#6610f2'
        }
    ];

    stats: Stat[] = [
        { value: '99.9%', label: 'Uptime', icon: 'fas fa-server' },
        { value: '<100ms', label: 'Tiempo de respuesta', icon: 'fas fa-bolt' },
        { value: '4+', label: 'Módulos integrados', icon: 'fas fa-cubes' },
        { value: '∞', label: 'Entidades soportadas', icon: 'fas fa-building' }
    ];

    testimonials: Testimonial[] = [
        {
            name: 'María González',
            role: 'Secretaria de Atención al Ciudadano',
            entity: 'Alcaldía Municipal',
            message: 'El sistema nos ha permitido reducir en un 60% el tiempo de respuesta a las PQRS. La ciudadanía ahora puede hacer seguimiento en tiempo real.',
            avatar: 'fas fa-user-circle'
        },
        {
            name: 'Carlos Ramírez',
            role: 'Director de Planeación',
            entity: 'Gobernación Departamental',
            message: 'Los reportes de contratación con IA nos dan insights que antes nos tomaban días analizar. Ahora en minutos tenemos decisiones informadas.',
            avatar: 'fas fa-user-tie'
        },
        {
            name: 'Ana Martínez',
            role: 'Coordinadora TI',
            entity: 'Municipio',
            message: 'La implementación fue rápida y el soporte técnico excelente. El sistema es intuitivo tanto para funcionarios como para ciudadanos.',
            avatar: 'fas fa-user-graduate'
        }
    ];

    benefits = [
        {
            title: 'Cumplimiento Normativo',
            description: 'Alineado con la Ley 1755 de 2015 y decretos reglamentarios de PQRS en Colombia.',
            icon: 'fas fa-gavel'
        },
        {
            title: 'Transparencia Total',
            description: 'Trazabilidad completa de todas las operaciones. Auditoría y reportes para entes de control.',
            icon: 'fas fa-eye'
        },
        {
            title: 'Ahorro de Tiempo',
            description: 'Automatización de procesos repetitivos. Reduce hasta 70% el tiempo administrativo.',
            icon: 'fas fa-clock'
        },
        {
            title: 'Satisfacción Ciudadana',
            description: 'Portal intuitivo y respuestas oportunas mejoran la percepción del servicio público.',
            icon: 'fas fa-smile'
        },
        {
            title: 'Escalable',
            description: 'Crece con tu entidad. Desde pequeños municipios hasta grandes gobernaciones.',
            icon: 'fas fa-expand-arrows-alt'
        },
        {
            title: 'Soporte Continuo',
            description: 'Actualizaciones regulares, nuevas funcionalidades y soporte técnico especializado.',
            icon: 'fas fa-life-ring'
        }
    ];

    useCases = [
        {
            title: 'Alcaldía Municipal',
            description: 'Gestión centralizada de PQRS de 50,000 habitantes, seguimiento de planes de desarrollo y consulta de contratación.',
            icon: 'fas fa-city',
            metrics: ['500+ PQRS/mes', '95% respuestas a tiempo', '10 usuarios activos']
        },
        {
            title: 'Gobernación',
            description: 'Coordinación multi-entidad con 20+ municipios, reportes consolidados y dashboard ejecutivo para el gobernador.',
            icon: 'fas fa-landmark',
            metrics: ['2000+ PQRS/mes', '15 planes institucionales', '100+ usuarios']
        },
        {
            title: 'Entidad Descentralizada',
            description: 'Hospital, universidad o empresa pública con necesidades específicas de atención ciudadana y transparencia.',
            icon: 'fas fa-hospital',
            metrics: ['Personalización completa', 'Integración con sistemas legacy', 'SLA garantizado']
        }
    ];

    techStack = [
        { name: 'Angular 18', icon: 'fab fa-angular', color: '#dd0031' },
        { name: 'FastAPI', icon: 'fas fa-rocket', color: '#009688' },
        { name: 'PostgreSQL', icon: 'fas fa-database', color: '#336791' },
        { name: 'Bootstrap 5', icon: 'fab fa-bootstrap', color: '#7952b3' },
        { name: 'Chart.js', icon: 'fas fa-chart-bar', color: '#ff6384' },
        { name: 'OpenAI', icon: 'fas fa-brain', color: '#412991' }
    ];

    constructor() { }

    ngOnInit(): void {
        // Animaciones de entrada
        this.animateOnScroll();
    }

    animateOnScroll(): void {
        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('animate-in');
                    }
                });
            },
            { threshold: 0.1 }
        );

        // Observar elementos con clase 'animate'
        setTimeout(() => {
            document.querySelectorAll('.animate').forEach((el) => observer.observe(el));
        }, 100);
    }

    scrollToSection(sectionId: string): void {
        const element = document.getElementById(sectionId);
        if (element) {
            element.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }
}
