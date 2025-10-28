from fastapi import APIRouter, Depends, HTTPException, status, Header
from pydantic import BaseModel
from typing import Optional
from app.utils.auth import require_superadmin
from app.config.settings import settings

# Importar funciones del script existente de reset
try:
    from scripts.reset_db import drop_and_recreate, create_schema_and_migrate, seed_superadmin
except Exception as e:
    # Fallback suave: lazily import dentro del handler para evitar fallos en import-time
    drop_and_recreate = None
    create_schema_and_migrate = None
    seed_superadmin = None


router = APIRouter(prefix="/maintenance", tags=["Mantenimiento"])


class ResetRequest(BaseModel):
    confirm: str


@router.post("/reset-db", include_in_schema=False)
def reset_database(
    body: ResetRequest,
    _: any = Depends(require_superadmin),
    x_maintenance_token: Optional[str] = Header(default=None, alias="X-Maintenance-Token"),
):
    """
    Resetea la base de datos a cero y crea solo el SUPERADMIN.
    Requisitos:
    - Autenticación como superadmin.
    - Confirmación exacta: settings.maintenance_confirm_phrase
    - (Opcional) Header X-Maintenance-Token si settings.maintenance_token está configurado.
    """

    # Verificar confirmación explícita
    if body.confirm != settings.maintenance_confirm_phrase:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Confirmación inválida. Verifica la frase de confirmación."
        )

    # Si se configuró un token, exigirlo
    if settings.maintenance_token:
        if not x_maintenance_token or x_maintenance_token != settings.maintenance_token:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Token de mantenimiento inválido o ausente"
            )

    # Importar funciones si el import previo falló
    global drop_and_recreate, create_schema_and_migrate, seed_superadmin
    if drop_and_recreate is None or create_schema_and_migrate is None or seed_superadmin is None:
        from scripts.reset_db import drop_and_recreate as _drop, create_schema_and_migrate as _migrate, seed_superadmin as _seed
        drop_and_recreate = _drop
        create_schema_and_migrate = _migrate
        seed_superadmin = _seed

    try:
        # Ejecutar reset de forma secuencial
        drop_and_recreate()
        create_schema_and_migrate()
        seed_superadmin()
    except Exception as e:
        # No exponer detalles en prod si settings.debug es False
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error ejecutando reset: {str(e) if settings.debug else 'Error interno'}"
        )

    return {
        "status": "ok",
        "message": "Reset completado. Sistema listo con solo SUPERADMIN.",
    }
