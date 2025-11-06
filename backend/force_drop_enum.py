"""
Script para forzar la eliminación del ENUM estadoplan y convertir la columna a TEXT
Ejecutar directamente en producción.
"""
import os
import psycopg2
from urllib.parse import urlparse

def force_drop_enum():
    """Fuerza la eliminación del ENUM y conversión a TEXT"""
    
    # Obtener URL de base de datos desde variables de entorno
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL no está configurada")
        return
    
    # Parse de la URL
    url = urlparse(database_url)
    
    try:
        # Conectar a PostgreSQL
        conn = psycopg2.connect(
            dbname=url.path[1:],
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port or 5432
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("✓ Conectado a la base de datos")
        
        # Paso 1: Verificar si la columna estado usa ENUM
        cursor.execute("""
            SELECT data_type, udt_name
            FROM information_schema.columns
            WHERE table_name = 'planes_institucionales'
            AND column_name = 'estado'
        """)
        result = cursor.fetchone()
        
        if result:
            data_type, udt_name = result
            print(f"  Columna estado: data_type={data_type}, udt_name={udt_name}")
            
            if data_type == 'USER-DEFINED' or udt_name == 'estadoplan':
                print("  ⚠ La columna estado usa ENUM, procediendo a convertir...")
                
                # Paso 2: Crear columna temporal como TEXT
                print("  1. Creando columna estado_temp TEXT...")
                cursor.execute("""
                    ALTER TABLE planes_institucionales 
                    ADD COLUMN IF NOT EXISTS estado_temp TEXT
                """)
                
                # Paso 3: Copiar y normalizar valores
                print("  2. Copiando y normalizando valores...")
                cursor.execute("""
                    UPDATE planes_institucionales 
                    SET estado_temp = CASE 
                        WHEN LOWER(estado::text) = 'formulacion' THEN 'formulacion'
                        WHEN LOWER(estado::text) = 'aprobado' THEN 'aprobado'
                        WHEN LOWER(estado::text) = 'en_ejecucion' THEN 'en_ejecucion'
                        WHEN LOWER(estado::text) = 'finalizado' THEN 'finalizado'
                        WHEN LOWER(estado::text) = 'suspendido' THEN 'suspendido'
                        WHEN LOWER(estado::text) = 'cancelado' THEN 'cancelado'
                        ELSE 'formulacion'
                    END
                    WHERE estado_temp IS NULL
                """)
                
                # Paso 4: Eliminar columna vieja
                print("  3. Eliminando columna estado vieja...")
                cursor.execute("""
                    ALTER TABLE planes_institucionales 
                    DROP COLUMN estado CASCADE
                """)
                
                # Paso 5: Renombrar columna temporal
                print("  4. Renombrando columna temporal...")
                cursor.execute("""
                    ALTER TABLE planes_institucionales 
                    RENAME COLUMN estado_temp TO estado
                """)
                
                # Paso 6: Agregar constraint NOT NULL
                print("  5. Agregando constraint NOT NULL...")
                cursor.execute("""
                    ALTER TABLE planes_institucionales 
                    ALTER COLUMN estado SET NOT NULL
                """)
                
                # Paso 7: Eliminar tipo ENUM si existe
                print("  6. Eliminando tipo ENUM estadoplan...")
                cursor.execute("""
                    DROP TYPE IF EXISTS estadoplan CASCADE
                """)
                
                print("✓ Columna estado convertida exitosamente a TEXT")
            else:
                print(f"✓ La columna estado ya es {data_type} (no usa ENUM)")
        else:
            print("❌ No se encontró la columna estado en planes_institucionales")
        
        # Verificar también estadocomponente si existe
        cursor.execute("""
            SELECT data_type, udt_name
            FROM information_schema.columns
            WHERE table_name = 'componentes_procesos'
            AND column_name = 'estado'
        """)
        result = cursor.fetchone()
        
        if result:
            data_type, udt_name = result
            print(f"\n  Columna componentes_procesos.estado: data_type={data_type}, udt_name={udt_name}")
            
            if data_type == 'USER-DEFINED' or udt_name == 'estadocomponente':
                print("  ⚠ La columna componentes_procesos.estado usa ENUM, procediendo a convertir...")
                
                cursor.execute("""
                    ALTER TABLE componentes_procesos 
                    ADD COLUMN IF NOT EXISTS estado_temp TEXT
                """)
                
                cursor.execute("""
                    UPDATE componentes_procesos 
                    SET estado_temp = LOWER(estado::text)
                    WHERE estado_temp IS NULL
                """)
                
                cursor.execute("""
                    ALTER TABLE componentes_procesos 
                    DROP COLUMN estado CASCADE
                """)
                
                cursor.execute("""
                    ALTER TABLE componentes_procesos 
                    RENAME COLUMN estado_temp TO estado
                """)
                
                cursor.execute("""
                    ALTER TABLE componentes_procesos 
                    ALTER COLUMN estado SET NOT NULL
                """)
                
                cursor.execute("""
                    DROP TYPE IF EXISTS estadocomponente CASCADE
                """)
                
                print("✓ Columna componentes_procesos.estado convertida exitosamente a TEXT")
        
        # Verificar resultado final
        print("\n=== VERIFICACIÓN FINAL ===")
        cursor.execute("""
            SELECT table_name, column_name, data_type, udt_name
            FROM information_schema.columns
            WHERE (table_name = 'planes_institucionales' OR table_name = 'componentes_procesos')
            AND column_name = 'estado'
        """)
        
        for row in cursor.fetchall():
            print(f"  {row[0]}.{row[1]}: {row[2]} ({row[3]})")
        
        # Verificar tipos ENUM restantes
        cursor.execute("""
            SELECT typname 
            FROM pg_type 
            WHERE typtype = 'e'
            AND typname IN ('estadoplan', 'estadocomponente')
        """)
        
        enums = cursor.fetchall()
        if enums:
            print(f"\n⚠ Tipos ENUM aún existentes: {[e[0] for e in enums]}")
        else:
            print("\n✓ No hay tipos ENUM estadoplan ni estadocomponente en la base de datos")
        
        cursor.close()
        conn.close()
        
        print("\n✓ Proceso completado exitosamente")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("=== FORZAR ELIMINACIÓN DE ENUM ESTADOPLAN ===\n")
    force_drop_enum()
