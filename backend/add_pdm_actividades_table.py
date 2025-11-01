"""
Script de migración para agregar la tabla pdm_actividades
Para actividades asociadas a productos del PDM
"""
from sqlalchemy import create_engine, text, inspect
from app.config.settings import settings
import sys


def run_migration():
    """Crear tabla pdm_actividades si no existe"""
    engine = create_engine(settings.database_url)
    inspector = inspect(engine)

    # Verificar si la tabla ya existe
    if 'pdm_actividades' in inspector.get_table_names():
        print("✓ La tabla 'pdm_actividades' ya existe. No se requiere migración.")
        return True

    print("Creando tabla 'pdm_actividades'...")

    try:
        with engine.connect() as conn:
            # Crear tabla pdm_actividades
            conn.execute(text("""
                CREATE TABLE pdm_actividades (
                    id SERIAL PRIMARY KEY,
                    entity_id INTEGER NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
                    codigo_indicador_producto VARCHAR(128) NOT NULL,
                    nombre VARCHAR(512) NOT NULL,
                    descripcion VARCHAR(1024),
                    responsable VARCHAR(256),
                    fecha_inicio TIMESTAMP,
                    fecha_fin TIMESTAMP,
                    porcentaje_avance FLOAT NOT NULL DEFAULT 0.0,
                    estado VARCHAR(64) NOT NULL DEFAULT 'pendiente',
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT uq_actividad_entity_codigo_nombre UNIQUE (entity_id, codigo_indicador_producto, nombre)
                )
            """))

            # Crear índices
            conn.execute(text("""
                CREATE INDEX idx_pdm_actividades_entity_id ON pdm_actividades(entity_id)
            """))

            conn.execute(text("""
                CREATE INDEX idx_pdm_actividades_codigo ON pdm_actividades(codigo_indicador_producto)
            """))

            conn.commit()
            print("✓ Tabla 'pdm_actividades' creada exitosamente con índices")
            return True

    except Exception as e:
        print(f"✗ Error al crear tabla: {e}")
        return False


if __name__ == "__main__":
    print("=== Migración: Agregar tabla pdm_actividades ===")
    success = run_migration()
    sys.exit(0 if success else 1)
