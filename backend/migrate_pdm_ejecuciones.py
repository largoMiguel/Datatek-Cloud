"""
Migración para agregar tabla pdm_actividades_ejecuciones y refactorizar evidencias.

Esta migración:
1. Crea la tabla pdm_actividades_ejecuciones (historial de avances)
2. Migra evidencias existentes de actividad_id a ejecucion_id
3. Crea una ejecución por cada actividad existente con valor_ejecutado > 0
4. Actualiza la tabla pdm_actividades_evidencias
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
import sys

# Configurar conexión a la base de datos
database_url = os.getenv("DATABASE_URL")
if not database_url:
    print("Error: DATABASE_URL no está configurada")
    sys.exit(1)

engine = create_engine(database_url)
Session = sessionmaker(bind=engine)


def run_migration():
    session = Session()
    
    try:
        print("=== Iniciando migración PDM Ejecuciones ===\n")
        
        # 1. Crear tabla pdm_actividades_ejecuciones
        print("1. Creando tabla pdm_actividades_ejecuciones...")
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS pdm_actividades_ejecuciones (
                id SERIAL PRIMARY KEY,
                actividad_id INTEGER NOT NULL REFERENCES pdm_actividades(id) ON DELETE CASCADE,
                entity_id INTEGER NOT NULL REFERENCES entities(id),
                valor_ejecutado_incremento DOUBLE PRECISION NOT NULL DEFAULT 0,
                descripcion VARCHAR(2048),
                url_evidencia VARCHAR(512),
                registrado_por VARCHAR(256),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        session.execute(text("CREATE INDEX IF NOT EXISTS idx_ejecuciones_actividad ON pdm_actividades_ejecuciones(actividad_id)"))
        session.execute(text("CREATE INDEX IF NOT EXISTS idx_ejecuciones_entity ON pdm_actividades_ejecuciones(entity_id)"))
        session.commit()
        print("   ✓ Tabla pdm_actividades_ejecuciones creada\n")
        
        # 2. Crear ejecuciones para actividades existentes con valor_ejecutado > 0
        print("2. Migrando actividades existentes a ejecuciones...")
        result = session.execute(text("""
            SELECT id, entity_id, valor_ejecutado, descripcion, created_at 
            FROM pdm_actividades 
            WHERE valor_ejecutado > 0
        """))
        
        actividades_con_valor = result.fetchall()
        print(f"   Encontradas {len(actividades_con_valor)} actividades con valor ejecutado")
        
        for actividad in actividades_con_valor:
            # Crear una ejecución por cada actividad con valor
            session.execute(text("""
                INSERT INTO pdm_actividades_ejecuciones 
                (actividad_id, entity_id, valor_ejecutado_incremento, descripcion, created_at, updated_at)
                VALUES (:actividad_id, :entity_id, :valor, :desc, :created, :created)
            """), {
                "actividad_id": actividad[0],
                "entity_id": actividad[1],
                "valor": actividad[2],
                "desc": actividad[3] or "Migración automática de valor ejecutado existente",
                "created": actividad[4]
            })
        
        session.commit()
        print(f"   ✓ Creadas {len(actividades_con_valor)} ejecuciones\n")
        
        # 3. Verificar si necesitamos migrar evidencias
        print("3. Verificando estructura de tabla pdm_actividades_evidencias...")
        
        # Verificar si existe la columna actividad_id (vieja estructura)
        result = session.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'pdm_actividades_evidencias' 
            AND column_name = 'actividad_id'
        """))
        
        tiene_actividad_id = result.fetchone() is not None
        
        if tiene_actividad_id:
            print("   Detectada estructura antigua, migrando evidencias...")
            
            # 3a. Crear tabla temporal nueva
            session.execute(text("""
                CREATE TABLE pdm_actividades_evidencias_new (
                    id SERIAL PRIMARY KEY,
                    ejecucion_id INTEGER NOT NULL REFERENCES pdm_actividades_ejecuciones(id) ON DELETE CASCADE,
                    entity_id INTEGER NOT NULL REFERENCES entities(id),
                    nombre_imagen VARCHAR(256) NOT NULL,
                    mime_type VARCHAR(64) NOT NULL,
                    tamano INTEGER NOT NULL,
                    contenido BYTEA NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # 3b. Migrar evidencias existentes
            # Por cada evidencia antigua, buscar la ejecución correspondiente a su actividad
            result = session.execute(text("""
                SELECT e.*, ej.id as ejecucion_id
                FROM pdm_actividades_evidencias e
                JOIN pdm_actividades_ejecuciones ej ON e.actividad_id = ej.actividad_id
                WHERE e.actividad_id IS NOT NULL
                ORDER BY e.created_at
            """))
            
            evidencias = result.fetchall()
            print(f"   Encontradas {len(evidencias)} evidencias para migrar")
            
            for ev in evidencias:
                session.execute(text("""
                    INSERT INTO pdm_actividades_evidencias_new 
                    (ejecucion_id, entity_id, nombre_imagen, mime_type, tamano, contenido, created_at, updated_at)
                    VALUES (:ej_id, :entity_id, :nombre, :mime, :tam, :cont, :created, :updated)
                """), {
                    "ej_id": ev[-1],  # ejecucion_id (último campo)
                    "entity_id": ev[2],  # entity_id
                    "nombre": ev[4] or 'evidencia.jpg',  # nombre_imagen
                    "mime": ev[5] or 'image/jpeg',  # mime_type
                    "tam": ev[6] or 0,  # tamano
                    "cont": ev[7],  # contenido
                    "created": ev[8],  # created_at
                    "updated": ev[9]   # updated_at
                })
            
            session.commit()
            
            # 3c. Eliminar tabla vieja y renombrar nueva
            session.execute(text("DROP TABLE pdm_actividades_evidencias"))
            session.execute(text("ALTER TABLE pdm_actividades_evidencias_new RENAME TO pdm_actividades_evidencias"))
            session.execute(text("CREATE INDEX IF NOT EXISTS idx_evidencias_ejecucion ON pdm_actividades_evidencias(ejecucion_id)"))
            session.commit()
            print(f"   ✓ Migradas {len(evidencias)} evidencias a nueva estructura\n")
        else:
            print("   ✓ Tabla pdm_actividades_evidencias ya tiene la estructura correcta\n")
        
        print("=== Migración completada exitosamente ===")
        
    except Exception as e:
        session.rollback()
        print(f"\n❌ Error durante la migración: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        session.close()


if __name__ == "__main__":
    run_migration()
