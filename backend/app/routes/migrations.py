"""
Endpoint de migración para actualizar base de datos en producción
Ejecutar: curl -X POST https://tu-backend.onrender.com/api/migrations/run -H "X-Migration-Key: TU_CLAVE_SECRETA"
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from sqlalchemy import text
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
    Ejecuta las migraciones pendientes para el módulo de Contratación.
    
    Cambios aplicados:
    - No se requieren cambios en la BD para este módulo (todo es frontend)
    - Este endpoint queda listo para futuras migraciones
    """
    try:
        migrations_applied = []
        
        # Verificar conexión
        db.execute(text("SELECT 1"))
        migrations_applied.append("✅ Conexión a base de datos verificada")
        
        # Las migraciones del módulo de Contratación no requieren cambios en BD
        # porque todo el procesamiento es en frontend consumiendo API externa (SECOP II)
        migrations_applied.append("✅ Módulo Contratación: No requiere cambios en BD (consume API externa)")
        
        # Commit de cambios si los hubiera
        db.commit()
        
        logger.info("Migraciones ejecutadas exitosamente")
        return {
            "status": "success",
            "message": "Migraciones ejecutadas correctamente",
            "migrations": migrations_applied,
            "details": "El módulo de Contratación no requiere migraciones de BD. Todos los cambios son en frontend."
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
            "last_migration": "Módulo Contratación - Frontend only",
            "notes": [
                "El módulo de Contratación no requiere cambios en la base de datos",
                "Todos los datos se obtienen de la API pública SECOP II en tiempo real",
                "Solo se usa el campo 'nit' de la tabla entities para hacer las consultas"
            ]
        }
        
        # Verificar que el campo NIT existe en entities
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'entities' AND column_name = 'nit'
        """))
        
        if result.fetchone():
            status_info["nit_field"] = "✅ Campo 'nit' existe en tabla entities"
        else:
            status_info["nit_field"] = "⚠️ Campo 'nit' no encontrado - se requiere migración"
            status_info["pending_migrations"].append("add_nit_column")
        
        return status_info
        
    except Exception as e:
        logger.error(f"Error verificando estado: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error verificando estado: {str(e)}"
        )
