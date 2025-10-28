"""
Script para agregar campos horario_atencion y tiempo_respuesta a la tabla entities.
"""

from sqlalchemy import create_engine, text, inspect
from app.config.settings import settings

def run_migration():
    """Ejecuta la migración para agregar campos de contacto"""
    
    print("🔄 Iniciando migración para agregar campos de contacto...")
    
    # Crear engine
    engine = create_engine(settings.database_url)
    
    try:
        inspector = inspect(engine)
        
        if not inspector.has_table('entities'):
            print("   ⚠️  La tabla entities no existe. Ejecuta primero migrate_to_entities.py")
            return
        
        columns = [c['name'] for c in inspector.get_columns('entities')]
        print(f"   📋 Columnas actuales: {', '.join(columns)}")
        
        fields_to_add = []
        if 'horario_atencion' not in columns:
            fields_to_add.append(('horario_atencion', 'VARCHAR(200)'))
        if 'tiempo_respuesta' not in columns:
            fields_to_add.append(('tiempo_respuesta', 'VARCHAR(100)'))
        
        if not fields_to_add:
            print("   ℹ️  Todos los campos ya existen")
            return
        
        with engine.connect() as conn:
            for field_name, field_type in fields_to_add:
                print(f"   📝 Agregando columna {field_name}...")
                conn.execute(text(f"ALTER TABLE entities ADD COLUMN {field_name} {field_type}"))
                print(f"   ✅ Columna {field_name} agregada")
            
            conn.commit()
        
        # Actualizar entidad por defecto con valores de ejemplo
        print("\n📝 Actualizando entidad por defecto con valores de ejemplo...")
        with engine.connect() as conn:
            conn.execute(text("""
                UPDATE entities 
                SET horario_atencion = 'Lunes a Viernes 8:00 AM - 5:00 PM',
                    tiempo_respuesta = 'Respuesta en 24 horas'
                WHERE code = 'DEFAULT' AND (horario_atencion IS NULL OR horario_atencion = '')
            """))
            conn.commit()
            print("   ✅ Entidad por defecto actualizada")
        
        print("\n✅ Migración completada exitosamente")
        
    except Exception as e:
        print(f"\n❌ Error durante la migración: {e}")
        import traceback
        print(traceback.format_exc())


if __name__ == "__main__":
    run_migration()
