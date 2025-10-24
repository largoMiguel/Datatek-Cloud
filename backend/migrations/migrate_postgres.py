#!/usr/bin/env python3
"""
Script de migración para agregar columnas de ciudadano a PostgreSQL en producción.
Este script se conecta a la base de datos de Render y ejecuta las migraciones necesarias.
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# URL de la base de datos desde variables de entorno
DATABASE_URL = os.getenv("DATABASE_URL", "").replace("postgres://", "postgresql://")

if not DATABASE_URL:
    print("❌ Error: DATABASE_URL no está configurada")
    sys.exit(1)

print(f"🔌 Conectando a la base de datos...")

try:
    # Crear engine
    engine = create_engine(DATABASE_URL, echo=True)
    
    # Crear sesión
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    print("\n✅ Conexión exitosa")
    
    # Paso 1: Agregar el valor 'CIUDADANO' al ENUM userrole
    print("\n📝 Paso 1: Agregando valor 'CIUDADANO' al ENUM userrole...")
    
    try:
        # Verificar si el valor ya existe
        check_enum = text("""
            SELECT EXISTS (
                SELECT 1
                FROM pg_enum
                WHERE enumlabel = 'CIUDADANO'
                AND enumtypid = (
                    SELECT oid
                    FROM pg_type
                    WHERE typname = 'userrole'
                )
            ) as exists;
        """)
        
        result = session.execute(check_enum).scalar()
        
        if not result:
            # El valor no existe, agregarlo
            # IMPORTANTE: ALTER TYPE ADD VALUE debe ejecutarse fuera de una transacción
            session.commit()  # Commit cualquier transacción pendiente
            
            add_enum_value = text("ALTER TYPE userrole ADD VALUE 'CIUDADANO'")
            
            # Usar connection sin transacción para ALTER TYPE
            with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
                conn.execute(add_enum_value)
                print("   ✅ Valor 'CIUDADANO' agregado al ENUM")
        else:
            print("   ℹ️  Valor 'CIUDADANO' ya existe en el ENUM")
    except Exception as e:
        print(f"   ⚠️  Error al modificar ENUM (puede ser normal si ya existe): {e}")
    
    # Paso 2: Agregar nuevas columnas
    print("\n📝 Paso 2: Agregando nuevas columnas...")
    
    migrations = [
        ("cedula", "ALTER TABLE users ADD COLUMN IF NOT EXISTS cedula VARCHAR(20)"),
        ("telefono", "ALTER TABLE users ADD COLUMN IF NOT EXISTS telefono VARCHAR(20)"),
        ("direccion", "ALTER TABLE users ADD COLUMN IF NOT EXISTS direccion VARCHAR(255)"),
    ]
    
    for column_name, sql in migrations:
        try:
            session.execute(text(sql))
            session.commit()
            print(f"   ✅ Columna '{column_name}' agregada")
        except Exception as e:
            session.rollback()
            print(f"   ⚠️  Error con columna '{column_name}': {e}")
    
    # Paso 3: Crear índice
    print("\n📝 Paso 3: Creando índice para cédula...")
    
    try:
        create_index = text("CREATE INDEX IF NOT EXISTS idx_users_cedula ON users(cedula)")
        session.execute(create_index)
        session.commit()
        print("   ✅ Índice creado")
    except Exception as e:
        session.rollback()
        print(f"   ⚠️  Error al crear índice: {e}")
    
    # Paso 4: Agregar comentarios
    print("\n📝 Paso 4: Agregando comentarios a las columnas...")
    
    comments = [
        "COMMENT ON COLUMN users.cedula IS 'Número de cédula de ciudadanía - usado para rol ciudadano'",
        "COMMENT ON COLUMN users.telefono IS 'Número de teléfono de contacto'",
        "COMMENT ON COLUMN users.direccion IS 'Dirección de residencia del ciudadano'",
    ]
    
    for comment_sql in comments:
        try:
            session.execute(text(comment_sql))
            session.commit()
            print(f"   ✅ Comentario agregado")
        except Exception as e:
            session.rollback()
            print(f"   ⚠️  Error al agregar comentario: {e}")
    
    # Verificación final
    print("\n📋 Verificación: Estructura de la tabla users")
    
    verify_sql = text("""
        SELECT 
            column_name, 
            data_type, 
            character_maximum_length,
            is_nullable
        FROM information_schema.columns
        WHERE table_name = 'users'
        ORDER BY ordinal_position;
    """)
    
    result = session.execute(verify_sql)
    print("\n" + "="*80)
    print(f"{'Columna':<25} {'Tipo':<20} {'Max Length':<12} {'Nullable':<10}")
    print("="*80)
    
    for row in result:
        length = row.character_maximum_length if row.character_maximum_length else "N/A"
        print(f"{row.column_name:<25} {row.data_type:<20} {str(length):<12} {row.is_nullable:<10}")
    
    print("="*80)
    
    print("\n✅ ¡Migración completada exitosamente!")
    
    session.close()

except Exception as e:
    print(f"\n❌ Error durante la migración: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
