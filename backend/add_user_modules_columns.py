#!/usr/bin/env python3
"""
Script para añadir las columnas user_type y allowed_modules a la tabla users.
Ejecutar una sola vez en producción después del deploy.
"""

from sqlalchemy import create_engine, text, inspect
from app.config.settings import settings

def add_user_modules_columns():
    """Añade columnas user_type y allowed_modules si no existen."""
    engine = create_engine(settings.database_url)
    
    with engine.connect() as conn:
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('users')]
        
        changes_made = []
        
        # Crear ENUM usertype si no existe (solo para PostgreSQL)
        if 'postgresql' in str(engine.url):
            try:
                check_enum = text("""
                    SELECT EXISTS (
                        SELECT 1 FROM pg_type WHERE typname = 'usertype'
                    ) as exists;
                """)
                enum_exists = conn.execute(check_enum).scalar()
                
                if not enum_exists:
                    conn.execute(text("CREATE TYPE usertype AS ENUM ('secretario', 'contratista')"))
                    conn.commit()
                    changes_made.append("✓ Creado ENUM usertype")
            except Exception as e:
                print(f"⚠️  Error creando ENUM usertype: {e}")
        
        # Añadir columna user_type
        if 'user_type' not in columns:
            try:
                if 'postgresql' in str(engine.url):
                    conn.execute(text("ALTER TABLE users ADD COLUMN user_type usertype NULL"))
                else:
                    conn.execute(text("ALTER TABLE users ADD COLUMN user_type VARCHAR(50) NULL"))
                conn.commit()
                changes_made.append("✓ Añadida columna user_type")
            except Exception as e:
                print(f"⚠️  Error añadiendo user_type: {e}")
        
        # Añadir columna allowed_modules
        if 'allowed_modules' not in columns:
            try:
                if 'postgresql' in str(engine.url):
                    conn.execute(text("ALTER TABLE users ADD COLUMN allowed_modules JSON NULL"))
                else:
                    conn.execute(text("ALTER TABLE users ADD COLUMN allowed_modules TEXT NULL"))
                conn.commit()
                changes_made.append("✓ Añadida columna allowed_modules")
            except Exception as e:
                print(f"⚠️  Error añadiendo allowed_modules: {e}")
        
        if changes_made:
            print("\n🎉 Migración completada:")
            for change in changes_made:
                print(f"   {change}")
        else:
            print("\n✅ Las columnas ya existen. No se requieren cambios.")

if __name__ == "__main__":
    print("🔧 Iniciando migración de columnas de usuarios...")
    add_user_modules_columns()
    print("\n✨ Proceso finalizado.")
