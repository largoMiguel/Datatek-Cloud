"""
Endpoint de migración para actualizar base de datos en producción
Ejecutar:
    curl -X POST https://<backend>/api/migrations/run -H "X-Migration-Key: <CLAVE>"
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy import inspect as sa_inspect
from app.config.database import get_db
from app.config.settings import settings
import logging

router = APIRouter(prefix="/migrations", tags=["migrations"])
logger = logging.getLogger(__name__)

# Clave secreta de migración (debe estar en variable de entorno)
MIGRATION_KEY = getattr(settings, 'migration_secret_key', "change-me-in-production")


def verify_migration_key(x_migration_key: str = Header(None)):
    """Verifica la clave de migración"""
    if not x_migration_key or x_migration_key != MIGRATION_KEY:
        raise HTTPException(status_code=403, detail="Clave de migración inválida")
    return True


@router.post("/run")
def run_migrations(
    db: Session = Depends(get_db),
    authorized: bool = Depends(verify_migration_key)
):
    """
    Ejecuta las migraciones pendientes relacionadas con:
    - Campo NIT en entities (para consultas SECOP II)
    - Flag enable_contratacion en entities
    - Permisos modulares: user_type y allowed_modules en users
    """
    try:
        migrations_applied = []

        # Verificar conexión
        db.execute(text("SELECT 1"))
        migrations_applied.append("✅ Conexión a base de datos verificada")

        # Inspeccionar esquema actual
        bind = db.get_bind()
        inspector = sa_inspect(bind)
        if not inspector.has_table("entities"):
            raise HTTPException(status_code=500, detail="La tabla 'entities' no existe. Ejecuta migraciones base primero.")

        existing_cols = {c["name"] for c in inspector.get_columns("entities")}
        is_postgres = bind.dialect.name.startswith("postgres")

        # 1) Agregar columna 'nit' si falta
        if "nit" not in existing_cols:
            if is_postgres:
                db.execute(text("ALTER TABLE entities ADD COLUMN IF NOT EXISTS nit VARCHAR(50)"))
                db.execute(text("CREATE INDEX IF NOT EXISTS ix_entities_nit ON entities (nit)"))
            else:
                # SQLite y otros: agregar columna e índice si no existen
                db.execute(text("ALTER TABLE entities ADD COLUMN nit VARCHAR(50)"))
                db.execute(text("CREATE INDEX IF NOT EXISTS ix_entities_nit ON entities (nit)"))
            migrations_applied.append("🆕 Agregada columna 'nit' en entities y creado índice")
        else:
            migrations_applied.append("ℹ️ Columna 'nit' ya existe en entities")

        # 2) Agregar flag 'enable_contratacion' si falta
        if "enable_contratacion" not in existing_cols:
            default_true = "TRUE" if is_postgres else "1"
            db.execute(text(f"ALTER TABLE entities ADD COLUMN enable_contratacion BOOLEAN NOT NULL DEFAULT {default_true}"))
            # Backfill explícito para filas existentes en algunos motores
            db.execute(text(f"UPDATE entities SET enable_contratacion = {default_true} WHERE enable_contratacion IS NULL"))
            migrations_applied.append("🆕 Agregada columna 'enable_contratacion' con valor por defecto TRUE")
        else:
            migrations_applied.append("ℹ️ Columna 'enable_contratacion' ya existe en entities")

        # ====== MIGRACIONES PARA PERMISOS MODULARES ======
        
        # Verificar que exista la tabla users
        if not inspector.has_table("users"):
            raise HTTPException(status_code=500, detail="La tabla 'users' no existe. Ejecuta migraciones base primero.")

        users_cols = {c["name"] for c in inspector.get_columns("users")}

        # 3) Agregar columna 'user_type' si falta
        if "user_type" not in users_cols:
            if is_postgres:
                # Crear ENUM type si no existe
                db.execute(text("""
                    DO $$ BEGIN
                        CREATE TYPE usertype AS ENUM ('secretario', 'contratista');
                    EXCEPTION
                        WHEN duplicate_object THEN null;
                    END $$;
                """))
                db.execute(text("ALTER TABLE users ADD COLUMN user_type usertype"))
            else:
                # SQLite: usar VARCHAR
                db.execute(text("ALTER TABLE users ADD COLUMN user_type VARCHAR(20)"))
            migrations_applied.append("🆕 Agregada columna 'user_type' en users (secretario/contratista)")
        else:
            migrations_applied.append("ℹ️ Columna 'user_type' ya existe en users")

        # 4) Agregar columna 'allowed_modules' si falta
        if "allowed_modules" not in users_cols:
            if is_postgres:
                # PostgreSQL: usar JSON o JSONB
                db.execute(text("ALTER TABLE users ADD COLUMN allowed_modules JSON"))
            else:
                # SQLite: usar TEXT para almacenar JSON
                db.execute(text("ALTER TABLE users ADD COLUMN allowed_modules TEXT"))
            migrations_applied.append("🆕 Agregada columna 'allowed_modules' en users (array JSON de módulos)")
        else:
            migrations_applied.append("ℹ️ Columna 'allowed_modules' ya existe en users")

        # 5) Normalizar valores existentes de user_type (MAYÚSCULAS -> minúsculas)
        if "user_type" in users_cols:
            # Contar registros a normalizar
            count_result = db.execute(text("""
                SELECT COUNT(*) 
                FROM users 
                WHERE user_type IN ('SECRETARIO', 'CONTRATISTA')
            """))
            count = count_result.scalar()
            
            if count and count > 0:
                # Actualizar SECRETARIO -> secretario
                db.execute(text("""
                    UPDATE users 
                    SET user_type = 'secretario' 
                    WHERE user_type = 'SECRETARIO'
                """))
                
                # Actualizar CONTRATISTA -> contratista
                db.execute(text("""
                    UPDATE users 
                    SET user_type = 'contratista' 
                    WHERE user_type = 'CONTRATISTA'
                """))
                
                migrations_applied.append(f"🔧 Normalizados {count} registros: user_type a minúsculas")
            else:
                migrations_applied.append("ℹ️ Valores de user_type ya están normalizados")

        # Commit de cambios
        db.commit()

        logger.info("Migraciones ejecutadas exitosamente")
        return {
            "status": "success",
            "message": "Migraciones ejecutadas correctamente",
            "migrations": migrations_applied,
            "details": "Migraciones aplicadas: NIT, enable_contratacion, user_type y allowed_modules (si estaban pendientes)."
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error ejecutando migraciones: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error ejecutando migraciones: {str(e)}"
        )


@router.get("/status")
def migration_status(
    db: Session = Depends(get_db),
    authorized: bool = Depends(verify_migration_key)
):
    """
    Verifica el estado de las migraciones y la base de datos
    """
    try:
        status_info = {
            "database_connection": "✅ Conectado",
            "pending_migrations": [],
            "last_migration": "Permisos modulares (user_type y allowed_modules)",
            "notes": [
                "El módulo de Contratación usa SECOP II (API externa)",
                "Se requiere el campo 'nit' en entities para consultar por NIT",
                "'enable_contratacion' controla la visibilidad del módulo",
                "Permisos modulares: asignar módulos específicos por usuario (secretario/contratista)"
            ]
        }

        bind = db.get_bind()
        inspector = sa_inspect(bind)
        if not inspector.has_table("entities"):
            status_info["database_connection"] = "⚠️ Sin tabla 'entities'"
            status_info["pending_migrations"].append("create_entities_table")
            return status_info

        cols = {c["name"] for c in inspector.get_columns("entities")}

        # Comprobar 'nit'
        if "nit" in cols:
            status_info["nit_field"] = "✅ Campo 'nit' existe en tabla entities"
        else:
            status_info["nit_field"] = "⚠️ Campo 'nit' no encontrado - se requiere migración"
            status_info["pending_migrations"].append("add_nit_column")

        # Comprobar 'enable_contratacion'
        if "enable_contratacion" in cols:
            status_info["enable_contratacion_field"] = "✅ Campo 'enable_contratacion' existe en entities"
        else:
            status_info["enable_contratacion_field"] = "⚠️ Campo 'enable_contratacion' no encontrado - se requiere migración"
            status_info["pending_migrations"].append("add_enable_contratacion_flag")

        # Comprobar tabla users
        if inspector.has_table("users"):
            users_cols = {c["name"] for c in inspector.get_columns("users")}
            
            # Comprobar 'user_type'
            if "user_type" in users_cols:
                status_info["user_type_field"] = "✅ Campo 'user_type' existe en tabla users"
            else:
                status_info["user_type_field"] = "⚠️ Campo 'user_type' no encontrado - se requiere migración"
                status_info["pending_migrations"].append("add_user_type_column")

            # Comprobar 'allowed_modules'
            if "allowed_modules" in users_cols:
                status_info["allowed_modules_field"] = "✅ Campo 'allowed_modules' existe en tabla users"
            else:
                status_info["allowed_modules_field"] = "⚠️ Campo 'allowed_modules' no encontrado - se requiere migración"
                status_info["pending_migrations"].append("add_allowed_modules_column")
        else:
            status_info["users_table"] = "⚠️ Tabla 'users' no encontrada"
            status_info["pending_migrations"].append("create_users_table")

        return status_info

    except Exception as e:
        logger.error(f"Error verificando estado: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error verificando estado: {str(e)}"
        )
