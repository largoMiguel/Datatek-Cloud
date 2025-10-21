from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.config.database import get_db
from app.models.plan import PlanInstitucional, Meta, EstadoPlan, EstadoMeta
from app.models.user import User, UserRole
from app.schemas import plan as plan_schemas
from app.utils.auth import get_current_user

router = APIRouter()


# ==================== ENDPOINTS PARA PLANES INSTITUCIONALES ====================

@router.get("/", response_model=List[plan_schemas.PlanInstitucional])
def listar_planes(
    anio: Optional[int] = Query(None, description="Filtrar por año"),
    estado: Optional[EstadoPlan] = Query(None, description="Filtrar por estado"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Listar todos los planes institucionales.
    Admins ven todos, secretarios también pueden ver todos los planes.
    """
    query = db.query(PlanInstitucional)
    
    if anio:
        query = query.filter(PlanInstitucional.anio == anio)
    
    if estado:
        query = query.filter(PlanInstitucional.estado == estado)
    
    return query.order_by(PlanInstitucional.anio.desc(), PlanInstitucional.id.desc()).all()


@router.get("/{plan_id}", response_model=plan_schemas.PlanInstitucionalConMetas)
def obtener_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtener un plan específico con todas sus metas.
    Las metas se filtran según el rol del usuario.
    """
    plan = db.query(PlanInstitucional).filter(PlanInstitucional.id == plan_id).first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    
    # Si es secretario, filtrar solo sus metas
    if current_user.role == UserRole.SECRETARIO and current_user.secretaria:
        metas_filtradas = [meta for meta in plan.metas if meta.responsable == current_user.secretaria]
        # Crear una copia del plan con metas filtradas
        plan_dict = {
            "id": plan.id,
            "nombre": plan.nombre,
            "descripcion": plan.descripcion,
            "anio": plan.anio,
            "fecha_inicio": plan.fecha_inicio,
            "fecha_fin": plan.fecha_fin,
            "estado": plan.estado,
            "metas": metas_filtradas
        }
        return plan_dict
    
    return plan


@router.post("/", response_model=plan_schemas.PlanInstitucional, status_code=status.HTTP_201_CREATED)
def crear_plan(
    plan_data: plan_schemas.PlanInstitucionalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Crear un nuevo plan institucional.
    Solo administradores pueden crear planes.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores pueden crear planes"
        )
    
    # Validar que fecha_fin sea posterior a fecha_inicio
    if plan_data.fecha_fin <= plan_data.fecha_inicio:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La fecha de fin debe ser posterior a la fecha de inicio"
        )
    
    nuevo_plan = PlanInstitucional(**plan_data.model_dump())
    db.add(nuevo_plan)
    db.commit()
    db.refresh(nuevo_plan)
    
    return nuevo_plan


@router.put("/{plan_id}", response_model=plan_schemas.PlanInstitucional)
def actualizar_plan(
    plan_id: int,
    plan_data: plan_schemas.PlanInstitucionalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Actualizar un plan institucional.
    Solo administradores pueden actualizar planes.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores pueden actualizar planes"
        )
    
    plan = db.query(PlanInstitucional).filter(PlanInstitucional.id == plan_id).first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    
    # Actualizar solo los campos proporcionados
    update_data = plan_data.model_dump(exclude_unset=True)
    
    # Validar fechas si se proporcionan ambas
    fecha_inicio = update_data.get('fecha_inicio', plan.fecha_inicio)
    fecha_fin = update_data.get('fecha_fin', plan.fecha_fin)
    
    if fecha_fin <= fecha_inicio:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La fecha de fin debe ser posterior a la fecha de inicio"
        )
    
    for field, value in update_data.items():
        setattr(plan, field, value)
    
    db.commit()
    db.refresh(plan)
    
    return plan


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Eliminar un plan institucional y todas sus metas asociadas.
    Solo administradores pueden eliminar planes.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores pueden eliminar planes"
        )
    
    plan = db.query(PlanInstitucional).filter(PlanInstitucional.id == plan_id).first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    
    db.delete(plan)
    db.commit()
    
    return None


# ==================== ENDPOINTS PARA METAS ====================

@router.get("/{plan_id}/metas", response_model=List[plan_schemas.Meta])
def listar_metas_del_plan(
    plan_id: int,
    estado: Optional[EstadoMeta] = Query(None, description="Filtrar por estado"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Listar todas las metas de un plan específico.
    Los secretarios solo ven sus propias metas.
    """
    # Verificar que el plan existe
    plan = db.query(PlanInstitucional).filter(PlanInstitucional.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    
    query = db.query(Meta).filter(Meta.plan_id == plan_id)
    
    # Filtrar por secretaría si es secretario
    if current_user.role == UserRole.SECRETARIO and current_user.secretaria:
        query = query.filter(Meta.responsable == current_user.secretaria)
    
    if estado:
        query = query.filter(Meta.estado == estado)
    
    return query.order_by(Meta.id).all()


@router.post("/{plan_id}/metas", response_model=plan_schemas.Meta, status_code=status.HTTP_201_CREATED)
def crear_meta(
    plan_id: int,
    meta_data: plan_schemas.MetaCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Crear una nueva meta para un plan.
    Admins pueden crear metas para cualquier secretaría.
    Secretarios solo pueden crear metas para su propia secretaría.
    """
    # Verificar que el plan existe
    plan = db.query(PlanInstitucional).filter(PlanInstitucional.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    
    # Validar que plan_id coincide
    if meta_data.plan_id != plan_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El plan_id en el cuerpo no coincide con el de la URL"
        )
    
    # Validar permisos: secretarios solo pueden crear metas para su secretaría
    if current_user.role == UserRole.SECRETARIO:
        if not current_user.secretaria:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tu usuario no tiene asignada una secretaría"
            )
        if meta_data.responsable != current_user.secretaria:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo puedes crear metas para tu propia secretaría"
            )
    
    # Validar fechas
    if meta_data.fecha_fin <= meta_data.fecha_inicio:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La fecha de fin debe ser posterior a la fecha de inicio"
        )
    
    # Validar avance
    if meta_data.avance_actual > meta_data.meta_numerica:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El avance actual no puede ser mayor que la meta numérica"
        )
    
    nueva_meta = Meta(**meta_data.model_dump())
    db.add(nueva_meta)
    db.commit()
    db.refresh(nueva_meta)
    
    return nueva_meta


@router.get("/metas/{meta_id}", response_model=plan_schemas.Meta)
def obtener_meta(
    meta_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtener una meta específica.
    Los secretarios solo pueden ver sus propias metas.
    """
    meta = db.query(Meta).filter(Meta.id == meta_id).first()
    
    if not meta:
        raise HTTPException(status_code=404, detail="Meta no encontrada")
    
    # Verificar permisos
    if current_user.role == UserRole.SECRETARIO and current_user.secretaria:
        if meta.responsable != current_user.secretaria:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para ver esta meta"
            )
    
    return meta


@router.put("/metas/{meta_id}", response_model=plan_schemas.Meta)
def actualizar_meta(
    meta_id: int,
    meta_data: plan_schemas.MetaUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Actualizar una meta existente.
    Admins pueden actualizar cualquier meta.
    Secretarios solo pueden actualizar sus propias metas.
    """
    meta = db.query(Meta).filter(Meta.id == meta_id).first()
    
    if not meta:
        raise HTTPException(status_code=404, detail="Meta no encontrada")
    
    # Verificar permisos
    if current_user.role == UserRole.SECRETARIO:
        if not current_user.secretaria:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tu usuario no tiene asignada una secretaría"
            )
        if meta.responsable != current_user.secretaria:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo puedes actualizar metas de tu propia secretaría"
            )
        # Secretarios no pueden cambiar el responsable
        if meta_data.responsable and meta_data.responsable != current_user.secretaria:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No puedes cambiar el responsable a otra secretaría"
            )
    
    # Actualizar solo los campos proporcionados
    update_data = meta_data.model_dump(exclude_unset=True)
    
    # Validar fechas si se proporcionan
    fecha_inicio = update_data.get('fecha_inicio', meta.fecha_inicio)
    fecha_fin = update_data.get('fecha_fin', meta.fecha_fin)
    
    if fecha_fin <= fecha_inicio:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La fecha de fin debe ser posterior a la fecha de inicio"
        )
    
    # Validar avance
    meta_numerica = update_data.get('meta_numerica', meta.meta_numerica)
    avance_actual = update_data.get('avance_actual', meta.avance_actual)
    
    if avance_actual > meta_numerica:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El avance actual no puede ser mayor que la meta numérica"
        )
    
    for field, value in update_data.items():
        setattr(meta, field, value)
    
    db.commit()
    db.refresh(meta)
    
    return meta


@router.delete("/metas/{meta_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_meta(
    meta_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Eliminar una meta.
    Admins pueden eliminar cualquier meta.
    Secretarios solo pueden eliminar sus propias metas.
    """
    meta = db.query(Meta).filter(Meta.id == meta_id).first()
    
    if not meta:
        raise HTTPException(status_code=404, detail="Meta no encontrada")
    
    # Verificar permisos
    if current_user.role == UserRole.SECRETARIO:
        if not current_user.secretaria:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tu usuario no tiene asignada una secretaría"
            )
        if meta.responsable != current_user.secretaria:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo puedes eliminar metas de tu propia secretaría"
            )
    
    db.delete(meta)
    db.commit()
    
    return None
