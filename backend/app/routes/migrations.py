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

        # Commit de cambios
        db.commit()

        logger.info("Migraciones ejecutadas exitosamente")
        return {
            "status": "success",
            "message": "Migraciones ejecutadas correctamente",
            "migrations": migrations_applied,
            "details": "Migraciones para NIT y enable_contratacion aplicadas (si estaban pendientes)."
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
            "last_migration": "NIT y enable_contratacion",
            "notes": [
                "El módulo de Contratación usa SECOP II (API externa)",
                "Se requiere el campo 'nit' en entities para consultar por NIT",
                "'enable_contratacion' controla la visibilidad del módulo"
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

        return status_info

    except Exception as e:
        logger.error(f"Error verificando estado: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error verificando estado: {str(e)}"
        )
