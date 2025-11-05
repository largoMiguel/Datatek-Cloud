"""
Migración para agregar tabla pdm_actividades_ejecuciones y refactorizar evidencias.

Esta migración:
1. Crea la tabla pdm_actividades_ejecuciones (historial de avances)
2. Migra evidencias existentes de actividad_id a ejecucion_id
3. Crea una ejecución por cada actividad existente con valor_ejecutado > 0
4. Actualiza la tabla pdm_actividades_evidencias
"""

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
import os
import sys


def run_migration():
    """Ejecuta la migración completa"""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL no está configurada")
    
    print("=== Iniciando migración PDM Ejecuciones ===\n")
    
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Verificar si la tabla pdm_actividades existe
        print("0. Verificando existencia de tablas...")
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        if 'pdm_actividades' not in tables:
            print("   ⚠ La tabla pdm_actividades no existe. Saltando migración.")
            print("   ℹ Esta migración solo es necesaria si ya tienes datos de PDM existentes.")
            session.close()
            return
        
        print("   ✓ Tablas encontradas\n")
        
        # 1. Crear tabla de ejecuciones
        print("1. Creando tabla pdm_actividades_ejecuciones...")
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS pdm_actividades_ejecuciones (
                id SERIAL PRIMARY KEY,
                actividad_id INTEGER NOT NULL,
                entity_id INTEGER NOT NULL,
                valor_ejecutado_incremento FLOAT NOT NULL,
                descripcion VARCHAR(2048),
                url_evidencia VARCHAR(512),
                registrado_por VARCHAR(256),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (actividad_id) REFERENCES pdm_actividades(id) ON DELETE CASCADE,
                FOREIGN KEY (entity_id) REFERENCES entities(id) ON DELETE CASCADE
            )
        """))
        session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_pdm_ejecuciones_actividad 
            ON pdm_actividades_ejecuciones(actividad_id)
        """))
        session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_pdm_ejecuciones_entity 
            ON pdm_actividades_ejecuciones(entity_id)
        """))
        session.commit()
        print("   ✓ Tabla pdm_actividades_ejecuciones creada\n")
        
        # 2. Migrar actividades existentes
        print("2. Migrando actividades existentes a ejecuciones...")
        result = session.execute(text("""
            SELECT id, entity_id, valor_ejecutado, descripcion, created_at 
            FROM pdm_actividades 
            WHERE valor_ejecutado > 0
        """))
        actividades = result.fetchall()
        
        count = 0
        for actividad in actividades:
            session.execute(text("""
                INSERT INTO pdm_actividades_ejecuciones 
                (actividad_id, entity_id, valor_ejecutado_incremento, descripcion, registrado_por, created_at, updated_at)
                VALUES (:actividad_id, :entity_id, :valor, :descripcion, 'Sistema - Migración', :created_at, :created_at)
            """), {
                'actividad_id': actividad[0],
                'entity_id': actividad[1],
                'valor': actividad[2],
                'descripcion': actividad[3] or 'Ejecución migrada automáticamente',
                'created_at': actividad[4]
            })
            count += 1
        
        session.commit()
        print(f"   ✓ Migradas {count} actividades a ejecuciones\n")
        
        # 3. Actualizar tabla de evidencias
        print("3. Actualizando estructura de tabla evidencias...")
        
        # Verificar si la tabla evidencias tiene la columna actividad_id
        result = session.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'pdm_actividades_evidencias' 
            AND column_name = 'actividad_id'
        """))
        
        if result.fetchone():
            print("   → Migrando evidencias de actividad_id a ejecucion_id...")
            
            # Crear tabla temporal con nueva estructura
            session.execute(text("""
                CREATE TABLE pdm_actividades_evidencias_new (
                    id SERIAL PRIMARY KEY,
                    ejecucion_id INTEGER NOT NULL,
                    entity_id INTEGER NOT NULL,
                    nombre_imagen VARCHAR(512) NOT NULL,
                    mime_type VARCHAR(128) NOT NULL,
                    tamano INTEGER NOT NULL,
                    contenido BYTEA NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (ejecucion_id) REFERENCES pdm_actividades_ejecuciones(id) ON DELETE CASCADE,
                    FOREIGN KEY (entity_id) REFERENCES entities(id) ON DELETE CASCADE
                )
            """))
            
            # Migrar evidencias existentes a la primera ejecución de cada actividad
            session.execute(text("""
                INSERT INTO pdm_actividades_evidencias_new 
                (ejecucion_id, entity_id, nombre_imagen, mime_type, tamano, contenido, created_at, updated_at)
                SELECT 
                    e.id as ejecucion_id,
                    ev.entity_id,
                    ev.nombre_imagen,
                    ev.mime_type,
                    ev.tamano,
                    ev.contenido,
                    ev.created_at,
                    ev.updated_at
                FROM pdm_actividades_evidencias ev
                INNER JOIN pdm_actividades_ejecuciones e ON e.actividad_id = ev.actividad_id
                WHERE ev.nombre_imagen IS NOT NULL 
                AND ev.mime_type IS NOT NULL 
                AND ev.tamano IS NOT NULL 
                AND ev.contenido IS NOT NULL
            """))
            
            # Eliminar tabla antigua
            session.execute(text("DROP TABLE pdm_actividades_evidencias"))
            
            # Renombrar tabla nueva
            session.execute(text("ALTER TABLE pdm_actividades_evidencias_new RENAME TO pdm_actividades_evidencias"))
            
            # Crear índices
            session.execute(text("""
                CREATE INDEX idx_pdm_evidencias_ejecucion 
                ON pdm_actividades_evidencias(ejecucion_id)
            """))
            session.execute(text("""
                CREATE INDEX idx_pdm_evidencias_entity 
                ON pdm_actividades_evidencias(entity_id)
            """))
            
            session.commit()
            print("   ✓ Evidencias migradas a nueva estructura\n")
        else:
            print("   ℹ La tabla evidencias ya tiene la estructura correcta\n")
        
        print("✓ Migración completada exitosamente\n")
        
    except Exception as e:
        session.rollback()
        print(f"\n❌ Error durante la migración: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    run_migration()
