from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.config.database import get_db
from app.models.entity import Entity
from app.models.user import User, UserRole
from app.models.pdm import PdmMetaAssignment, PdmAvance, PdmActividad
from app.schemas.pdm import (
    AssignmentUpsertRequest,
    AssignmentResponse,
    AssignmentsMapResponse,
    AvanceUpsertRequest,
    AvanceResponse,
    AvancesListResponse,
    ActividadCreateRequest,
    ActividadUpdateRequest,
    ActividadResponse,
    ActividadesListResponse,
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


@router.get("/{slug}/actividades", response_model=ActividadesListResponse)
async def get_actividades(
    slug: str,
    codigo: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    entity = get_entity_or_404(db, slug)
    ensure_user_can_manage_entity(current_user, entity)

    rows = db.query(PdmActividad).filter(
        PdmActividad.entity_id == entity.id,
        PdmActividad.codigo_indicador_producto == codigo,
    ).order_by(PdmActividad.created_at.desc()).all()

    return ActividadesListResponse(
        codigo_indicador_producto=codigo,
        actividades=[
            ActividadResponse(
                id=row.id,
                entity_id=row.entity_id,
                codigo_indicador_producto=row.codigo_indicador_producto,
                nombre=row.nombre,
                descripcion=row.descripcion,
                responsable=row.responsable,
                fecha_inicio=row.fecha_inicio.isoformat() if row.fecha_inicio else None,
                fecha_fin=row.fecha_fin.isoformat() if row.fecha_fin else None,
                porcentaje_avance=row.porcentaje_avance,
                estado=row.estado,
                created_at=row.created_at.isoformat() if row.created_at else '',
                updated_at=row.updated_at.isoformat() if row.updated_at else '',
            )
            for row in rows
        ],
    )


@router.post("/{slug}/actividades", response_model=ActividadResponse, status_code=status.HTTP_201_CREATED)
async def create_actividad(
    slug: str,
    payload: ActividadCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    entity = get_entity_or_404(db, slug)
    ensure_user_can_manage_entity(current_user, entity)

    from datetime import datetime as dt

    nueva_actividad = PdmActividad(
        entity_id=entity.id,
        codigo_indicador_producto=payload.codigo_indicador_producto,
        nombre=payload.nombre,
        descripcion=payload.descripcion,
        responsable=payload.responsable,
        fecha_inicio=dt.fromisoformat(payload.fecha_inicio) if payload.fecha_inicio else None,
        fecha_fin=dt.fromisoformat(payload.fecha_fin) if payload.fecha_fin else None,
        porcentaje_avance=payload.porcentaje_avance,
        estado=payload.estado,
    )

    db.add(nueva_actividad)
    db.commit()
    db.refresh(nueva_actividad)

    return ActividadResponse(
        id=nueva_actividad.id,
        entity_id=nueva_actividad.entity_id,
        codigo_indicador_producto=nueva_actividad.codigo_indicador_producto,
        nombre=nueva_actividad.nombre,
        descripcion=nueva_actividad.descripcion,
        responsable=nueva_actividad.responsable,
        fecha_inicio=nueva_actividad.fecha_inicio.isoformat() if nueva_actividad.fecha_inicio else None,
        fecha_fin=nueva_actividad.fecha_fin.isoformat() if nueva_actividad.fecha_fin else None,
        porcentaje_avance=nueva_actividad.porcentaje_avance,
        estado=nueva_actividad.estado,
        created_at=nueva_actividad.created_at.isoformat() if nueva_actividad.created_at else '',
        updated_at=nueva_actividad.updated_at.isoformat() if nueva_actividad.updated_at else '',
    )


@router.put("/{slug}/actividades/{actividad_id}", response_model=ActividadResponse)
async def update_actividad(
    slug: str,
    actividad_id: int,
    payload: ActividadUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    entity = get_entity_or_404(db, slug)
    ensure_user_can_manage_entity(current_user, entity)

    actividad = db.query(PdmActividad).filter(
        PdmActividad.id == actividad_id,
        PdmActividad.entity_id == entity.id,
    ).first()

    if not actividad:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Actividad no encontrada")

    from datetime import datetime as dt

    if payload.nombre is not None:
        actividad.nombre = payload.nombre
    if payload.descripcion is not None:
        actividad.descripcion = payload.descripcion
    if payload.responsable is not None:
        actividad.responsable = payload.responsable
    if payload.fecha_inicio is not None:
        actividad.fecha_inicio = dt.fromisoformat(payload.fecha_inicio) if payload.fecha_inicio else None
    if payload.fecha_fin is not None:
        actividad.fecha_fin = dt.fromisoformat(payload.fecha_fin) if payload.fecha_fin else None
    if payload.porcentaje_avance is not None:
        actividad.porcentaje_avance = payload.porcentaje_avance
    if payload.estado is not None:
        actividad.estado = payload.estado

    db.commit()
    db.refresh(actividad)

    return ActividadResponse(
        id=actividad.id,
        entity_id=actividad.entity_id,
        codigo_indicador_producto=actividad.codigo_indicador_producto,
        nombre=actividad.nombre,
        descripcion=actividad.descripcion,
        responsable=actividad.responsable,
        fecha_inicio=actividad.fecha_inicio.isoformat() if actividad.fecha_inicio else None,
        fecha_fin=actividad.fecha_fin.isoformat() if actividad.fecha_fin else None,
        porcentaje_avance=actividad.porcentaje_avance,
        estado=actividad.estado,
        created_at=actividad.created_at.isoformat() if actividad.created_at else '',
        updated_at=actividad.updated_at.isoformat() if actividad.updated_at else '',
    )


@router.delete("/{slug}/actividades/{actividad_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_actividad(
    slug: str,
    actividad_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    entity = get_entity_or_404(db, slug)
    ensure_user_can_manage_entity(current_user, entity)

    actividad = db.query(PdmActividad).filter(
        PdmActividad.id == actividad_id,
        PdmActividad.entity_id == entity.id,
    ).first()

    if not actividad:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Actividad no encontrada")

    db.delete(actividad)
    db.commit()
    return None
