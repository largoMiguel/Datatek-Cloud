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
                estado=row.estado,
                anio=row.anio if row.anio is not None else 0,
                meta_ejecutar=row.meta_ejecutar if row.meta_ejecutar is not None else 0.0,
                valor_ejecutado=row.valor_ejecutado if row.valor_ejecutado is not None else 0.0,
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
    from datetime import datetime

    # Validaciones de negocio
    if payload.fecha_inicio and not payload.fecha_fin:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Si diligencias fecha_inicio debes diligenciar fecha_fin")
    if payload.fecha_fin and not payload.fecha_inicio:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Si diligencias fecha_fin debes diligenciar fecha_inicio")
    if payload.fecha_inicio and payload.fecha_fin:
        try:
            d1 = datetime.fromisoformat(payload.fecha_inicio)
            d2 = datetime.fromisoformat(payload.fecha_fin)
            if d1 > d2:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="La fecha de inicio no puede ser mayor a la fecha de fin")
        except ValueError:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Formato de fecha inválido. Use ISO 8601 (YYYY-MM-DD)")
    # Validar estado permitido
    estados_permitidos = {"pendiente", "en_progreso", "completada", "cancelada"}
    if payload.estado and payload.estado not in estados_permitidos:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Estado inválido para actividad")

    # Validaciones de anio/meta
    if payload.anio < 2000 or payload.anio > 2100:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Año de ejecución inválido")
    if payload.meta_ejecutar < 0:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="La meta a ejecutar debe ser >= 0")
    if payload.valor_ejecutado < 0:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="El valor ejecutado debe ser >= 0")

    nueva_actividad = PdmActividad(
        entity_id=entity.id,
        codigo_indicador_producto=payload.codigo_indicador_producto,
        nombre=payload.nombre,
        descripcion=payload.descripcion,
        responsable=(payload.responsable or None),
        fecha_inicio=dt.fromisoformat(payload.fecha_inicio) if payload.fecha_inicio else None,
        fecha_fin=dt.fromisoformat(payload.fecha_fin) if payload.fecha_fin else None,
        estado=payload.estado,
        anio=payload.anio,
        meta_ejecutar=payload.meta_ejecutar,
        valor_ejecutado=payload.valor_ejecutado,
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
        estado=nueva_actividad.estado,
        anio=nueva_actividad.anio if nueva_actividad.anio is not None else 0,
        meta_ejecutar=nueva_actividad.meta_ejecutar,
        valor_ejecutado=nueva_actividad.valor_ejecutado,
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
        actividad.responsable = (payload.responsable or None)
    if payload.fecha_inicio is not None:
        actividad.fecha_inicio = dt.fromisoformat(payload.fecha_inicio) if payload.fecha_inicio else None
    if payload.fecha_fin is not None:
        actividad.fecha_fin = dt.fromisoformat(payload.fecha_fin) if payload.fecha_fin else None
    if payload.anio is not None:
        actividad.anio = payload.anio
    if payload.meta_ejecutar is not None:
        actividad.meta_ejecutar = payload.meta_ejecutar
    if payload.valor_ejecutado is not None:
        actividad.valor_ejecutado = payload.valor_ejecutado
    if payload.estado is not None:
        estados_permitidos = {"pendiente", "en_progreso", "completada", "cancelada"}
        if payload.estado not in estados_permitidos:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Estado inválido para actividad")
        actividad.estado = payload.estado

    # Validar consistencia de fechas cuando ambas presentes
    if actividad.fecha_inicio and actividad.fecha_fin and actividad.fecha_inicio > actividad.fecha_fin:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="La fecha de inicio no puede ser mayor a la fecha de fin")

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
        estado=actividad.estado,
        anio=actividad.anio if actividad.anio is not None else 0,
        meta_ejecutar=actividad.meta_ejecutar,
        valor_ejecutado=actividad.valor_ejecutado,
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
