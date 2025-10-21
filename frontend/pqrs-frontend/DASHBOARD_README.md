# Dashboard PQRS - Nueva UI Profesional

## 🎨 Características del Nuevo Diseño

### Interfaz Moderna y Profesional
- **Sidebar lateral fijo** con navegación intuitiva
- **Gradientes modernos** y colores vibrantes
- **Animaciones suaves** en transiciones y hover effects
- **Diseño responsive** que se adapta a móviles y tablets
- **Dark sidebar** con iconos de Font Awesome

### Estadísticas en Tiempo Real
- **4 Cards de métricas** principales con iconos y tendencias
- **Total de PQRS** con contador del mes
- **PQRS Pendientes** que requieren atención
- **PQRS En Proceso** en gestión activa
- **PQRS Resueltas** completadas exitosamente

### Gráficos Interactivos (Chart.js)
1. **Gráfico de Dona (Doughnut)**: Distribución por estado de PQRS
2. **Gráfico de Barras**: PQRS clasificadas por tipo (Petición, Queja, Reclamo, Sugerencia)
3. **Gráfico de Línea**: Tendencia de los últimos 7 días

### Tablas Mejoradas
- **Diseño moderno** con hover effects
- **Badges de estado** con colores distintivos
- **Botones de acción** con tooltips informativos
- **Información clara** y organizada

### Formularios Estilizados
- **Diseño en grid** de 2 columnas
- **Iconos descriptivos** en cada campo
- **Validación visual** con estados de focus
- **Placeholders informativos**

### Sistema de Colores
- **Primary**: Azul brillante (#3b82f6)
- **Success**: Verde esmeralda (#10b981)
- **Warning**: Amarillo ámbar (#f59e0b)
- **Danger**: Rojo coral (#ef4444)
- **Info**: Cian vibrante (#06b6d4)

## 🚀 Cómo Ejecutar

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend/pqrs-frontend
npm install
npm start
```

La aplicación estará disponible en:
- Frontend: http://localhost:4200
- Backend: http://localhost:8000

## 📦 Dependencias Nuevas Instaladas

- `chart.js`: ^4.x - Librería de gráficos interactivos
- `ng2-charts`: ^6.x - Wrapper de Chart.js para Angular

## 🎯 Funcionalidades Implementadas

### Dashboard Analytics
- Visualización de estadísticas en tiempo real
- Gráficos interactivos con Chart.js
- Cards de métricas con animaciones
- Tabla de PQRS recientes (últimas 10)

### Gestión de PQRS
- Listado completo con filtros por vista
- Asignación a secretarios (solo admin)
- Cambio de estado con modal interactivo
- Creación de nuevas PQRS con formulario mejorado

### Gestión de Usuarios
- Listado de usuarios del sistema
- Toggle de estado activo/inactivo
- Badges distintivos para roles (Admin/Secretario)
- Protección para no desactivar usuario actual

## 💡 Mejoras Visuales

1. **Sidebar con degradado oscuro** y efectos de hover
2. **Cards con sombras** y animaciones de elevación
3. **Badges con bordes** y colores distintivos
4. **Botones con gradientes** y efectos de hover
5. **Modales rediseñados** con headers coloridos
6. **Estados vacíos** con iconos y mensajes amigables
7. **Spinners de carga** personalizados
8. **Scrollbar personalizado** más elegante

## 🔧 Archivos Modificados

- `dashboard.ts`: Agregados métodos de estadísticas y gráficos
- `dashboard.html`: Rediseño completo con sidebar y nueva estructura
- `dashboard.scss`: Estilos profesionales con variables y animaciones
- `styles.scss`: Agregados Font Awesome y scrollbar personalizado
- `package.json`: Agregadas dependencias de Chart.js

## 📱 Responsive Design

El diseño se adapta a diferentes tamaños de pantalla:

- **Desktop** (>1200px): Vista completa con sidebar expandido
- **Tablet** (768px-1200px): Ajustes de grid y espaciado
- **Mobile** (<768px): Sidebar colapsado con solo iconos, tablas scrollables

## 🎨 Paleta de Colores Utilizada

```scss
$primary-color: #3b82f6;    // Azul brillante
$secondary-color: #64748b;  // Gris pizarra
$success-color: #10b981;    // Verde esmeralda
$warning-color: #f59e0b;    // Amarillo ámbar
$danger-color: #ef4444;     // Rojo coral
$info-color: #06b6d4;       // Cian vibrante
$dark-color: #1e293b;       // Azul oscuro
$light-bg: #f8fafc;         // Gris claro
```

## ✨ Animaciones Implementadas

- Transiciones suaves en botones y cards
- Fade-in al cambiar de vista
- Rotación en botón de cierre de modales
- Elevación en hover de cards
- Spin en iconos de carga
- Deslizamiento en items del sidebar

## 🎯 Próximas Mejoras Sugeridas

1. Agregar modo oscuro (dark theme)
2. Exportar reportes en PDF
3. Notificaciones en tiempo real
4. Búsqueda y filtrado avanzado
5. Paginación en tablas
6. Vista de calendario para PQRS
7. Chat interno para seguimiento

---

**Desarrollado con** ❤️ **usando Angular + FastAPI**
