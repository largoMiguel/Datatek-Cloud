#!/usr/bin/env python3
"""
Script para verificar y corregir los valores del enum tiposolicitud en PostgreSQL
"""
import os
import sys

# Agregar el directorio backend al path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

from sqlalchemy import text
from app.config.database import engine

def check_and_fix_enum():
    """Verifica y corrige los valores del enum tiposolicitud"""
    
    print("\n🔍 Verificando enum tiposolicitud en PostgreSQL...\n")
    
    try:
        with engine.connect() as conn:
            # Verificar valores actuales del enum
            check_query = text("""
                SELECT enumlabel 
                FROM pg_enum 
                WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'tiposolicitud')
                ORDER BY enumsortorder;
            """)
            
            result = conn.execute(check_query)
            current_values = [row[0] for row in result.fetchall()]
            
            print(f"📋 Valores actuales en enum tiposolicitud:")
            for value in current_values:
                print(f"   • {value}")
            
            # Valores esperados (minúsculas según el modelo Python)
            expected_values = ['peticion', 'queja', 'reclamo', 'sugerencia']
            
            print(f"\n📋 Valores esperados:")
            for value in expected_values:
                print(f"   • {value}")
            
            # Comparar
            if set(current_values) == set(expected_values):
                print("\n✅ Enum está correcto, no se necesitan cambios")
                return True
            
            print("\n⚠️  Valores no coinciden, se requiere corrección")
            print("\n🔄 Aplicando corrección...")
            
            # Estrategia: Eliminar la columna, el enum, y recrearlos con valores correctos
            
            # Paso 1: Eliminar la columna tipo_solicitud
            print("   1. Eliminando columna tipo_solicitud...")
            conn.execute(text("ALTER TABLE pqrs DROP COLUMN IF EXISTS tipo_solicitud CASCADE"))
            conn.commit()
            
            # Paso 2: Eliminar el enum antiguo
            print("   2. Eliminando enum tiposolicitud antiguo...")
            conn.execute(text("DROP TYPE IF EXISTS tiposolicitud CASCADE"))
            conn.commit()
            
            # Paso 3: Crear el enum con valores correctos (minúsculas)
            print("   3. Creando enum tiposolicitud con valores correctos...")
            conn.execute(text("CREATE TYPE tiposolicitud AS ENUM ('peticion', 'queja', 'reclamo', 'sugerencia')"))
            conn.commit()
            
            # Paso 4: Recrear la columna
            print("   4. Recreando columna tipo_solicitud...")
            conn.execute(text("ALTER TABLE pqrs ADD COLUMN tipo_solicitud tiposolicitud NOT NULL DEFAULT 'peticion'"))
            conn.commit()
            
            print("\n✅ Corrección completada exitosamente")
            
            # Verificar nuevamente
            result = conn.execute(check_query)
            new_values = [row[0] for row in result.fetchall()]
            
            print(f"\n📋 Valores después de la corrección:")
            for value in new_values:
                print(f"   • {value}")
            
            return True
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def check_other_enums():
    """Verifica otros enums por si tienen el mismo problema"""
    
    print("\n🔍 Verificando otros enums...\n")
    
    enums_to_check = {
        'estadopqrs': ['pendiente', 'en_proceso', 'resuelto', 'cerrado'],
        'tipoidentificacion': ['personal', 'anonima'],
        'mediorespuesta': ['email', 'fisica', 'telefono', 'ticket']
    }
    
    try:
        with engine.connect() as conn:
            for enum_name, expected_values in enums_to_check.items():
                check_query = text(f"""
                    SELECT enumlabel 
                    FROM pg_enum 
                    WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = '{enum_name}')
                    ORDER BY enumsortorder;
                """)
                
                result = conn.execute(check_query)
                current_values = [row[0] for row in result.fetchall()]
                
                if current_values:
                    status = "✅" if set(current_values) == set(expected_values) else "⚠️"
                    print(f"{status} {enum_name}: {current_values}")
                else:
                    print(f"❌ {enum_name}: NO EXISTE")
    
    except Exception as e:
        print(f"❌ Error verificando enums: {e}")

if __name__ == "__main__":
    success = check_and_fix_enum()
    check_other_enums()
    sys.exit(0 if success else 1)
