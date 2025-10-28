"""
Script de migración para agregar entity_id a las tablas pqrs y planes_institucionales
Usa la URL de base de datos configurada en settings (SQLite o PostgreSQL).
"""
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from app.config.settings import settings
from app.models.entity import Entity
import sys


def migrate_database():
    """Agrega la columna entity_id a pqrs y planes_institucionales usando SQLAlchemy"""

    print("🔄 Iniciando migración para agregar entity_id...")

    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        insp = inspect(engine)

        # Validar existencia de tablas base
        if not insp.has_table('entities'):
            print("❌ La tabla 'entities' no existe. Ejecuta primero migrate_to_entities.py")
            return False
        if not insp.has_table('pqrs'):
            print("❌ La tabla 'pqrs' no existe.")
            return False
        if not insp.has_table('planes_institucionales'):
            print("❌ La tabla 'planes_institucionales' no existe.")
            return False

        # Obtener entidad por defecto activa (o crear una)
        row = db.query(Entity.id).filter(Entity.is_active == True).order_by(Entity.id.asc()).first()
        default_entity_id = row[0] if row else None
        if not default_entity_id:
            # Crear una por defecto mínima
            from app.models.entity import Entity as EntityModel
            default = EntityModel(name='Entidad Principal', code='DEFAULT', slug='entidad-principal', is_active=True)
            db.add(default)
            db.commit()
            db.refresh(default)
            default_entity_id = default.id
            print(f"ℹ️  Entidad por defecto creada con ID {default_entity_id}")
        else:
            print(f"ℹ️  Usando entidad ID {default_entity_id} como valor por defecto")

        is_postgres = 'postgresql' in str(engine.url)

        with engine.begin() as conn:
            # PQRS
            pqrs_cols = [c['name'] for c in insp.get_columns('pqrs')]
            if 'entity_id' not in pqrs_cols:
                print("📝 Agregando entity_id a tabla pqrs...")
                if is_postgres:
                    conn.execute(text("""
                        ALTER TABLE pqrs
                        ADD COLUMN IF NOT EXISTS entity_id INTEGER REFERENCES entities(id) ON DELETE CASCADE
                    """))
                else:
                    # SQLite: agregar columna sin NOT NULL primero
                    conn.execute(text("ALTER TABLE pqrs ADD COLUMN entity_id INTEGER"))

                # Backfill
                conn.execute(text("UPDATE pqrs SET entity_id = :eid WHERE entity_id IS NULL"), {"eid": default_entity_id})

                # Índice
                if is_postgres:
                    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_pqrs_entity_id ON pqrs(entity_id)"))
                else:
                    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_pqrs_entity_id ON pqrs(entity_id)"))
                print("   ✅ Columna entity_id agregada y poblada en pqrs")
            else:
                print("ℹ️  La columna entity_id ya existe en pqrs")

            # PLANES
            planes_cols = [c['name'] for c in insp.get_columns('planes_institucionales')]
            if 'entity_id' not in planes_cols:
                print("📝 Agregando entity_id a tabla planes_institucionales...")
                if is_postgres:
                    conn.execute(text("""
                        ALTER TABLE planes_institucionales
                        ADD COLUMN IF NOT EXISTS entity_id INTEGER REFERENCES entities(id) ON DELETE CASCADE
                    """))
                else:
                    conn.execute(text("ALTER TABLE planes_institucionales ADD COLUMN entity_id INTEGER"))

                conn.execute(text("UPDATE planes_institucionales SET entity_id = :eid WHERE entity_id IS NULL"), {"eid": default_entity_id})

                if is_postgres:
                    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_planes_entity_id ON planes_institucionales(entity_id)"))
                else:
                    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_planes_entity_id ON planes_institucionales(entity_id)"))
                print("   ✅ Columna entity_id agregada y poblada en planes_institucionales")
            else:
                print("ℹ️  La columna entity_id ya existe en planes_institucionales")

        print("✅ Migración completada exitosamente")
        return True
    except Exception as e:
        print(f"❌ Error durante la migración: {e}")
        import traceback
        print(traceback.format_exc())
        return False
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("MIGRACIÓN: Agregar entity_id a PQRS y Planes")
    print("=" * 60)

    success = migrate_database()

    if success:
        print("\n✅ Migración completada. Puedes ejecutar la aplicación ahora.")
        sys.exit(0)
    else:
        print("\n❌ La migración falló. Revisa los errores arriba.")
        sys.exit(1)
