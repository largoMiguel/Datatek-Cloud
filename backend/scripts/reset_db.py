#!/usr/bin/env python3
"""
Script para RESETEAR la base de datos a cero y crear únicamente el SUPERADMIN.
- Para PostgreSQL: elimina el schema public y lo recrea.
- Para SQLite: elimina el archivo .db y recrea.

USO (¡Peligroso en producción!):
  python scripts/reset_db.py

Variables de entorno relevantes (app.config.settings):
  - database_url
  - superadmin_username
  - superadmin_email
  - superadmin_password
"""
import os
import sys
from sqlalchemy import text
from app.config.settings import settings
from app.config.database import engine, Base, get_db
from app.models.user import User, UserRole
from app.utils.auth import get_password_hash
from app.main import run_postgres_migration, run_sqlite_migration


def log(msg: str):
    print(msg, flush=True)


def drop_and_recreate():
    url = str(engine.url)
    if 'postgresql' in url:
        log("\n⚠️  Reseteando base de datos PostgreSQL (DROP SCHEMA public CASCADE)...")
        with engine.connect() as conn:
            conn.execute(text("COMMIT"))
            conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
            conn.execute(text("CREATE SCHEMA public"))
            conn.execute(text("GRANT ALL ON SCHEMA public TO postgres"))
            conn.execute(text("GRANT ALL ON SCHEMA public TO public"))
            conn.commit()
        log("   ✅ Schema 'public' recreado")
    elif 'sqlite' in url:
        # Intentar eliminar archivo físico
        try:
            db_path = url.replace('sqlite:///','')
            if os.path.exists(db_path):
                os.remove(db_path)
                log(f"   ✅ Archivo SQLite eliminado: {db_path}")
        except Exception as e:
            log(f"   ⚠️  No se pudo eliminar SQLite: {e}")
    else:
        log(f"❌ Motor no soportado para reset: {url}")
        sys.exit(1)


def create_schema_and_migrate():
    # Crear tablas básicas
    Base.metadata.create_all(bind=engine)
    # Ejecutar migraciones auxiliares
    run_postgres_migration()
    run_sqlite_migration()
    log("   ✅ Migraciones aplicadas")


def seed_superadmin():
    db = next(get_db())
    try:
        # Borrar cualquier usuario existente por seguridad del enunciado
        db.query(User).delete()
        db.commit()
        username = settings.superadmin_username
        email = settings.superadmin_email
        password = settings.superadmin_password
        hashed = get_password_hash(password)
        superadmin = User(
            username=username,
            email=email,
            full_name="Super Administrador",
            hashed_password=hashed,
            role=UserRole.SUPERADMIN,
            entity_id=None,
            secretaria=None
        )
        db.add(superadmin)
        db.commit()
        log(f"   ✅ Superadmin creado: {username}")
    finally:
        db.close()


def main():
    confirm = os.environ.get('CONFIRM_RESET', 'false').lower() in ('1','true','yes','y')
    if not confirm:
        log("❌ Por seguridad, establece CONFIRM_RESET=true para ejecutar este script.")
        sys.exit(2)
    log("\n==== RESET DB INICIADO ====")
    log(f"URL de BD: {engine.url}")
    drop_and_recreate()
    create_schema_and_migrate()
    seed_superadmin()
    log("\n✅ Reset completado. Sistema listo con solo SUPERADMIN.")

if __name__ == '__main__':
    main()
