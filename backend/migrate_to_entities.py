"""
Script de migración para agregar la tabla de entidades y actualizar usuarios.
Este script debe ejecutarse una sola vez para migrar de la estructura antigua a la nueva.
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config.settings import settings
from app.models.user import User, UserRole
from app.models.entity import Entity
from app.config.database import Base
import sys

def run_migration():
    """Ejecuta la migración de la base de datos"""
    
    print("🔄 Iniciando migración de base de datos...")
    
    # Crear engine
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # 1. Agregar el nuevo rol SUPERADMIN al enum si es PostgreSQL
        if 'postgresql' in str(engine.url):
            print("\n📝 Agregando rol SUPERADMIN al enum...")
            try:
                with engine.connect() as conn:
                    # Verificar si el valor ya existe
                    check = text("""
                        SELECT EXISTS (
                            SELECT 1 FROM pg_enum
                            WHERE enumlabel = 'superadmin'
                            AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'userrole')
                        );
                    """)
                    exists = conn.execute(check).scalar()
                    
                    if not exists:
                        conn.execute(text("COMMIT"))
                        conn.execute(text("ALTER TYPE userrole ADD VALUE 'superadmin'"))
                        print("   ✅ Rol SUPERADMIN agregado")
                    else:
                        print("   ℹ️  Rol SUPERADMIN ya existe")
            except Exception as e:
                print(f"   ⚠️  Error agregando rol: {e}")
        
        # 2. Crear tabla de entidades
        print("\n📝 Creando tabla de entidades...")
        Base.metadata.create_all(bind=engine, tables=[Entity.__table__])
        print("   ✅ Tabla entities creada")
        
        # 2.1. Agregar columnas nuevas a entities si no existen (slug y logo_url)
        print("\n📝 Verificando columnas de entities...")
        try:
            from sqlalchemy import inspect
            inspector = inspect(engine)
            
            if inspector.has_table('entities'):
                columns = [c['name'] for c in inspector.get_columns('entities')]
                
                # Si faltan las columnas slug o logo_url, recrear la tabla
                if 'slug' not in columns or 'logo_url' not in columns:
                    print("   ⚠️  Faltan columnas en entities - recreando tabla...")
                    
                    with engine.connect() as conn:
                        # Crear tabla temporal con todas las columnas
                        conn.execute(text("""
                            CREATE TABLE entities_new (
                                id INTEGER PRIMARY KEY,
                                name VARCHAR(200) NOT NULL UNIQUE,
                                code VARCHAR(50) NOT NULL UNIQUE,
                                slug VARCHAR(100) NOT NULL UNIQUE,
                                description TEXT,
                                address VARCHAR(300),
                                phone VARCHAR(50),
                                email VARCHAR(150),
                                logo_url VARCHAR(500),
                                is_active BOOLEAN NOT NULL DEFAULT 1,
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                updated_at TIMESTAMP
                            )
                        """))
                        
                        # Copiar datos existentes y generar slugs
                        existing_entities = conn.execute(
                            text("SELECT id, name, code, description, address, phone, email, is_active, created_at, updated_at FROM entities")
                        ).fetchall()
                        
                        import re
                        for entity in existing_entities:
                            entity_id, name, code, description, address, phone, email, is_active, created_at, updated_at = entity
                            
                            # Generar slug desde el nombre
                            slug = name.lower() if name else code.lower()
                            slug = slug.replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
                            slug = slug.replace('ñ', 'n')
                            slug = re.sub(r'[^a-z0-9\s-]', '', slug)
                            slug = re.sub(r'\s+', '-', slug.strip())
                            slug = re.sub(r'-+', '-', slug)
                            
                            conn.execute(text("""
                                INSERT INTO entities_new 
                                (id, name, code, slug, description, address, phone, email, is_active, created_at, updated_at)
                                VALUES (:id, :name, :code, :slug, :description, :address, :phone, :email, :is_active, :created_at, :updated_at)
                            """), {
                                "id": entity_id,
                                "name": name,
                                "code": code,
                                "slug": slug,
                                "description": description,
                                "address": address,
                                "phone": phone,
                                "email": email,
                                "is_active": is_active,
                                "created_at": created_at,
                                "updated_at": updated_at
                            })
                        
                        # Eliminar tabla antigua
                        conn.execute(text("DROP TABLE entities"))
                        
                        # Renombrar nueva tabla
                        conn.execute(text("ALTER TABLE entities_new RENAME TO entities"))
                        
                        conn.commit()
                    print("   ✅ Tabla entities recreada con columnas slug y logo_url")
                else:
                    print("   ℹ️  Todas las columnas ya existen")
        except Exception as e:
            print(f"   ⚠️  Error verificando/agregando columnas: {e}")
            import traceback
            print(traceback.format_exc())
        
        # 3. Agregar columna entity_id a users si no existe
        print("\n📝 Agregando columna entity_id a users...")
        try:
            if 'postgresql' in str(engine.url):
                with engine.connect() as conn:
                    conn.execute(text("""
                        ALTER TABLE users 
                        ADD COLUMN IF NOT EXISTS entity_id INTEGER 
                        REFERENCES entities(id) ON DELETE CASCADE
                    """))
                    conn.commit()
                print("   ✅ Columna entity_id agregada")
            elif 'sqlite' in str(engine.url):
                # Para SQLite, necesitamos verificar si la columna ya existe
                from sqlalchemy import inspect
                inspector = inspect(engine)
                columns = [c['name'] for c in inspector.get_columns('users')]
                
                if 'entity_id' not in columns:
                    # SQLite no soporta ADD COLUMN con FK directamente
                    # Necesitamos recrear la tabla
                    print("   ⚠️  SQLite detectado - recreando tabla users...")
                    
                    with engine.connect() as conn:
                        # Crear tabla temporal
                        conn.execute(text("""
                            CREATE TABLE users_new (
                                id INTEGER PRIMARY KEY,
                                username VARCHAR NOT NULL UNIQUE,
                                email VARCHAR NOT NULL UNIQUE,
                                full_name VARCHAR NOT NULL,
                                hashed_password VARCHAR NOT NULL,
                                role VARCHAR NOT NULL,
                                entity_id INTEGER,
                                secretaria VARCHAR,
                                cedula VARCHAR,
                                telefono VARCHAR,
                                direccion VARCHAR,
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                updated_at TIMESTAMP,
                                is_active BOOLEAN NOT NULL DEFAULT 1,
                                FOREIGN KEY (entity_id) REFERENCES entities(id) ON DELETE CASCADE
                            )
                        """))
                        
                        # Copiar datos
                        conn.execute(text("""
                            INSERT INTO users_new 
                            (id, username, email, full_name, hashed_password, role, 
                             secretaria, cedula, telefono, direccion, created_at, updated_at, is_active)
                            SELECT id, username, email, full_name, hashed_password, role,
                                   secretaria, cedula, telefono, direccion, created_at, updated_at, is_active
                            FROM users
                        """))
                        
                        # Eliminar tabla antigua
                        conn.execute(text("DROP TABLE users"))
                        
                        # Renombrar nueva tabla
                        conn.execute(text("ALTER TABLE users_new RENAME TO users"))
                        
                        conn.commit()
                    print("   ✅ Tabla users recreada con columna entity_id")
                else:
                    print("   ℹ️  Columna entity_id ya existe")
        except Exception as e:
            print(f"   ⚠️  Error agregando columna: {e}")
            import traceback
            print(traceback.format_exc())
        
        # 4. Crear entidad por defecto para usuarios existentes
        print("\n📝 Creando entidad por defecto...")
        
        # Buscar o crear la entidad por defecto usando ORM (ahora la tabla ya tiene slug)
        default_entity = db.query(Entity).filter(Entity.code == "DEFAULT").first()
        
        if not default_entity:
            default_entity = Entity(
                name="Entidad Principal",
                code="DEFAULT",
                slug="entidad-principal",
                description="Entidad creada automáticamente para migración de usuarios existentes",
                is_active=True
            )
            db.add(default_entity)
            db.commit()
            db.refresh(default_entity)
            print(f"   ✅ Entidad por defecto creada (ID: {default_entity.id})")
        else:
            print(f"   ℹ️  Entidad por defecto ya existe (ID: {default_entity.id})")
        
        # 5. Asignar usuarios admin y secretarios existentes a la entidad por defecto
        print("\n📝 Asignando usuarios existentes a entidad por defecto...")
        users_updated = db.query(User).filter(
            User.role.in_([UserRole.ADMIN, UserRole.SECRETARIO]),
            User.entity_id == None
        ).update(
            {"entity_id": default_entity.id},
            synchronize_session=False
        )
        db.commit()
        print(f"   ✅ {users_updated} usuarios asignados a entidad por defecto")
        
        # 6. Mostrar resumen
        print("\n📊 Resumen de migración:")
        total_entities = db.query(Entity).count()
        total_users = db.query(User).count()
        total_admins = db.query(User).filter(User.role == UserRole.ADMIN).count()
        total_secretarios = db.query(User).filter(User.role == UserRole.SECRETARIO).count()
        total_superadmins = db.query(User).filter(User.role == UserRole.SUPERADMIN).count()
        
        print(f"   - Entidades: {total_entities}")
        print(f"   - Usuarios totales: {total_users}")
        print(f"   - Super administradores: {total_superadmins}")
        print(f"   - Administradores: {total_admins}")
        print(f"   - Secretarios: {total_secretarios}")
        
        print("\n✅ Migración completada exitosamente")
        print("\n⚠️  PRÓXIMOS PASOS:")
        print("   1. Ejecutar: POST /api/auth/init-superadmin para crear el super administrador")
        print("   2. Iniciar sesión con: superadmin / superadmin123")
        print("   3. Cambiar la contraseña inmediatamente")
        print("   4. Acceder a /soft-admin para gestionar entidades")
        
    except Exception as e:
        print(f"\n❌ Error durante la migración: {e}")
        import traceback
        print(traceback.format_exc())
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    run_migration()
