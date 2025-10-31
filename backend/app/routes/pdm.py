from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.config.database import get_db
from app.models.entity import Entity
from app.models.user import User, UserRole
from app.models.pdm import PdmMetaAssignment, PdmAvance
from app.schemas.pdm import (
    AssignmentUpsertRequest,
    AssignmentResponse,
    AssignmentsMapResponse,
    AvanceUpsertRequest,
    AvanceResponse,
    AvancesListResponse,
)
from app.utils.auth import get_current_active_user

router = APIRouter(prefix="/pdm")


def get_entity_or_404(db: Session, slug: str) -> Entity:
    entity = db.query(Entity).filter(Entity.slug == slug, Entity.is_active == True).first()
    if not entity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entidad no encontrada o inactiva")
    return entity


def ensure_user_can_manage_entity(current_user: User, entity: Entity):
    if current_user.role == UserRole.SUPERADMIN:
        return
    if not current_user.entity_id or current_user.entity_id != entity.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado para gestionar esta entidad")


@router.get("/{slug}/assignments", response_model=AssignmentsMapResponse)
async def get_assignments(
    slug: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    entity = get_entity_or_404(db, slug)
    ensure_user_can_manage_entity(current_user, entity)

    rows = db.query(PdmMetaAssignment).filter(PdmMetaAssignment.entity_id == entity.id).all()
    mapping = {r.codigo_indicador_producto: r.secretaria for r in rows}
    return {"assignments": mapping}


@router.post("/{slug}/assignments", response_model=AssignmentResponse)
async def upsert_assignment(
    slug: str,
    payload: AssignmentUpsertRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    entity = get_entity_or_404(db, slug)
    ensure_user_can_manage_entity(current_user, entity)

    rec = db.query(PdmMetaAssignment).filter(
        PdmMetaAssignment.entity_id == entity.id,
        PdmMetaAssignment.codigo_indicador_producto == payload.codigo_indicador_producto,
    ).first()
    if rec:
        rec.secretaria = payload.secretaria
    else:
        rec = PdmMetaAssignment(
            entity_id=entity.id,
            codigo_indicador_producto=payload.codigo_indicador_producto,
            secretaria=payload.secretaria,
        )
        db.add(rec)
    db.commit()
    db.refresh(rec)
    return AssignmentResponse(
        entity_id=rec.entity_id,
        codigo_indicador_producto=rec.codigo_indicador_producto,
        secretaria=rec.secretaria,
    )


@router.get("/{slug}/avances", response_model=AvancesListResponse)
async def get_avances(
    slug: str,
    codigo: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    entity = get_entity_or_404(db, slug)
    ensure_user_can_manage_entity(current_user, entity)

    rows = db.query(PdmAvance).filter(
        PdmAvance.entity_id == entity.id,
        PdmAvance.codigo_indicador_producto == codigo,
    ).all()

    return AvancesListResponse(
        codigo_indicador_producto=codigo,
        avances=[
            AvanceResponse(
                entity_id=row.entity_id,
                codigo_indicador_producto=row.codigo_indicador_producto,
                anio=row.anio,
                valor_ejecutado=row.valor_ejecutado,
                comentario=row.comentario,
            )
            for row in rows
        ],
    )


@router.post("/{slug}/avances", response_model=AvanceResponse)
async def upsert_avance(
    slug: str,
    payload: AvanceUpsertRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    entity = get_entity_or_404(db, slug)
    ensure_user_can_manage_entity(current_user, entity)

    row = db.query(PdmAvance).filter(
        PdmAvance.entity_id == entity.id,
        PdmAvance.codigo_indicador_producto == payload.codigo_indicador_producto,
        PdmAvance.anio == payload.anio,
    ).first()

    if row:
        row.valor_ejecutado = payload.valor_ejecutado
        row.comentario = payload.comentario
    else:
        row = PdmAvance(
            entity_id=entity.id,
            codigo_indicador_producto=payload.codigo_indicador_producto,
            anio=payload.anio,
            valor_ejecutado=payload.valor_ejecutado,
            comentario=payload.comentario,
        )
        db.add(row)

    db.commit()
    db.refresh(row)

    return AvanceResponse(
        entity_id=row.entity_id,
        codigo_indicador_producto=row.codigo_indicador_producto,
        anio=row.anio,
        valor_ejecutado=row.valor_ejecutado,
        comentario=row.comentario,
    )
