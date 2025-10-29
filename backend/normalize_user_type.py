"""
Script para normalizar valores de user_type en la base de datos.
Convierte 'SECRETARIO', 'CONTRATISTA' a minúsculas.

Uso:
    python normalize_user_type.py
"""
import sys
import os

# Agregar el directorio backend al path para importar módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from app.config.settings import settings

def normalize_user_types():
    """Normaliza los valores de user_type a minúsculas"""
    
    # Crear engine de base de datos
    engine = create_engine(settings.database_url)
    
    try:
        with engine.connect() as conn:
            # Iniciar transacción
            trans = conn.begin()
            
            try:
                # Verificar si la columna existe
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='users' AND column_name='user_type'
                """))
                
                if not result.fetchone():
                    print("⚠️  La columna 'user_type' no existe en la tabla 'users'")
                    print("   Ejecuta primero la migración: POST /api/migrations/run")
                    return
                
                # Contar registros a actualizar
                count_result = conn.execute(text("""
                    SELECT COUNT(*) 
                    FROM users 
                    WHERE user_type IN ('SECRETARIO', 'CONTRATISTA')
                """))
                count = count_result.scalar()
                
                if count == 0:
                    print("✅ No hay registros para normalizar")
                    return
                
                print(f"📊 Encontrados {count} registros con user_type en mayúsculas")
                
                # Actualizar SECRETARIO -> secretario
                result = conn.execute(text("""
                    UPDATE users 
                    SET user_type = 'secretario' 
                    WHERE user_type = 'SECRETARIO'
                """))
                secretarios_updated = result.rowcount
                
                # Actualizar CONTRATISTA -> contratista
                result = conn.execute(text("""
                    UPDATE users 
                    SET user_type = 'contratista' 
                    WHERE user_type = 'CONTRATISTA'
                """))
                contratistas_updated = result.rowcount
                
                # Commit de la transacción
                trans.commit()
                
                print(f"✅ Normalización completada:")
                print(f"   - {secretarios_updated} SECRETARIO → secretario")
                print(f"   - {contratistas_updated} CONTRATISTA → contratista")
                print(f"   - Total: {secretarios_updated + contratistas_updated} registros actualizados")
                
            except Exception as e:
                # Rollback en caso de error
                trans.rollback()
                print(f"❌ Error durante la normalización: {e}")
                raise
                
    except Exception as e:
        print(f"❌ Error conectando a la base de datos: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("🔄 Iniciando normalización de user_type...")
    print(f"   Base de datos: {settings.database_url.split('@')[-1] if '@' in settings.database_url else 'local'}")
    print()
    
    normalize_user_types()
    
    print()
    print("✨ Proceso completado")
