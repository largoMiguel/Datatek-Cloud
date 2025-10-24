from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime
from app.config.database import get_db
from app.models.pqrs import PQRS, EstadoPQRS
from app.models.user import User, UserRole
from app.schemas.pqrs import PQRSCreate, PQRSUpdate, PQRS as PQRSSchema, PQRSWithDetails, PQRSResponse
from app.utils.auth import get_current_active_user, require_admin
from app.utils.helpers import generate_radicado

router = APIRouter(prefix="/pqrs", tags=["PQRS"])

@router.post("/", response_model=PQRSSchema)
async def create_pqrs(
    pqrs_data: PQRSCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_active_user)
):
    """Crear nueva PQRS"""
    # Usar número de radicado proporcionado o generar uno nuevo
    if pqrs_data.numero_radicado:
        numero_radicado = pqrs_data.numero_radicado
    else:
        numero_radicado = generate_radicado()
        while db.query(PQRS).filter(PQRS.numero_radicado == numero_radicado).first():
            numero_radicado = generate_radicado()
    
    # Verificar que el número de radicado no exista
    existing_pqrs = db.query(PQRS).filter(PQRS.numero_radicado == numero_radicado).first()
    if existing_pqrs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El número de radicado {numero_radicado} ya existe"
        )
    
    # Crear PQRS sin asignar (assigned_to_id será NULL hasta que admin/secretario la asigne)
    db_pqrs = PQRS(
        numero_radicado=numero_radicado,
        nombre_ciudadano=pqrs_data.nombre_ciudadano,
        cedula_ciudadano=pqrs_data.cedula_ciudadano,
        telefono_ciudadano=pqrs_data.telefono_ciudadano,
        email_ciudadano=pqrs_data.email_ciudadano,
        direccion_ciudadano=pqrs_data.direccion_ciudadano,
        tipo_solicitud=pqrs_data.tipo_solicitud,
        asunto=pqrs_data.asunto,
        descripcion=pqrs_data.descripcion,
        created_by_id=current_user.id,
        assigned_to_id=None  # Sin asignar inicialmente
    )
    
    db.add(db_pqrs)
    db.commit()
    db.refresh(db_pqrs)
    
    return db_pqrs

@router.get("/", response_model=List[PQRSWithDetails])
async def get_pqrs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    estado: Optional[EstadoPQRS] = None,
    assigned_to_me: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtener lista de PQRS"""
    query = db.query(PQRS).options(
        joinedload(PQRS.created_by),
        joinedload(PQRS.assigned_to)
    )
    
    # Filtrar según rol
    if current_user.role == UserRole.ADMIN:
        # Admin ve todas, opcionalmente solo las asignadas a él
        if assigned_to_me:
            query = query.filter(PQRS.assigned_to_id == current_user.id)
    elif current_user.role == UserRole.SECRETARIO:
        # Secretarios solo ven PQRS asignadas a ellos
        query = query.filter(PQRS.assigned_to_id == current_user.id)
    elif current_user.role == UserRole.CIUDADANO:
        # Ciudadanos ven PQRS que ellos crearon (basándose en created_by_id)
        # O que coincidan con su cédula/email
        query = query.filter(
            (PQRS.created_by_id == current_user.id) |
            (PQRS.cedula_ciudadano == current_user.cedula) |
            (PQRS.email_ciudadano == current_user.email)
        )
    
    # Filtrar por estado si se especifica
    if estado:
        query = query.filter(PQRS.estado == estado)
    
    # Ordenar por fecha de creación (más recientes primero)
    query = query.order_by(PQRS.created_at.desc())
    
    pqrs_list = query.offset(skip).limit(limit).all()
    
    # Convertir a formato con detalles
    result = []
    for pqrs in pqrs_list:
        pqrs_dict = {
            **pqrs.__dict__,
            "created_by": {
                "id": pqrs.created_by.id,
                "username": pqrs.created_by.username,
                "full_name": pqrs.created_by.full_name
            } if pqrs.created_by else None,
            "assigned_to": {
                "id": pqrs.assigned_to.id,
                "username": pqrs.assigned_to.username,
                "full_name": pqrs.assigned_to.full_name
            } if pqrs.assigned_to else None
        }
        result.append(pqrs_dict)
    
    return result

@router.get("/{pqrs_id}", response_model=PQRSWithDetails)
async def get_pqrs_by_id(
    pqrs_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_active_user)
):
    """Obtener PQRS por ID"""
    pqrs = db.query(PQRS).options(
        joinedload(PQRS.created_by),
        joinedload(PQRS.assigned_to)
    ).filter(PQRS.id == pqrs_id).first()
    
    if not pqrs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PQRS no encontrada"
        )
    
    # Verificar permisos
    if current_user.role != UserRole.ADMIN and pqrs.assigned_to_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para ver esta PQRS"
        )
    
    return {
        **pqrs.__dict__,
        "created_by": {
            "id": pqrs.created_by.id,
            "username": pqrs.created_by.username,
            "full_name": pqrs.created_by.full_name
        } if pqrs.created_by else None,
        "assigned_to": {
            "id": pqrs.assigned_to.id,
            "username": pqrs.assigned_to.username,
            "full_name": pqrs.assigned_to.full_name
        } if pqrs.assigned_to else None
    }

@router.put("/{pqrs_id}", response_model=PQRSSchema)
async def update_pqrs(
    pqrs_id: int,
    pqrs_update: PQRSUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Actualizar PQRS"""
    pqrs = db.query(PQRS).filter(PQRS.id == pqrs_id).first()
    
    if not pqrs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PQRS no encontrada"
        )
    
    # Verificar permisos
    if current_user.role != UserRole.ADMIN and pqrs.assigned_to_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para editar esta PQRS"
        )
    
    # Actualizar campos
    update_data = pqrs_update.dict(exclude_unset=True)
    
    # Manejar cambios de estado
    if "estado" in update_data:
        if update_data["estado"] == EstadoPQRS.CERRADO and not pqrs.fecha_cierre:
            pqrs.fecha_cierre = datetime.utcnow()
        if update_data["estado"] == EstadoPQRS.RESUELTO and not pqrs.fecha_respuesta:
            pqrs.fecha_respuesta = datetime.utcnow()
    
    # Solo admin puede asignar PQRS
    if "assigned_to_id" in update_data and current_user.role != UserRole.ADMIN:
        del update_data["assigned_to_id"]
    elif "assigned_to_id" in update_data and not pqrs.fecha_delegacion:
        pqrs.fecha_delegacion = datetime.utcnow()
    
    for field, value in update_data.items():
        setattr(pqrs, field, value)
    
    db.commit()
    db.refresh(pqrs)
    
    return pqrs

@router.post("/{pqrs_id}/assign")
async def assign_pqrs(
    pqrs_id: int,
    assigned_to_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Asignar PQRS a un usuario (solo admin)"""
    pqrs = db.query(PQRS).filter(PQRS.id == pqrs_id).first()
    
    if not pqrs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PQRS no encontrada"
        )
    
    # Verificar que el usuario existe
    assigned_user = db.query(User).filter(User.id == assigned_to_id).first()
    if not assigned_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    pqrs.assigned_to_id = assigned_to_id
    if not pqrs.fecha_delegacion:
        pqrs.fecha_delegacion = datetime.utcnow()
    
    db.commit()
    
    return {"message": f"PQRS asignada a {assigned_user.full_name}"}

@router.post("/{pqrs_id}/respond", response_model=PQRSSchema)
async def respond_pqrs(
    pqrs_id: int,
    response_data: PQRSResponse,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Responder PQRS"""
    pqrs = db.query(PQRS).filter(PQRS.id == pqrs_id).first()
    
    if not pqrs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PQRS no encontrada"
        )
    
    # Verificar permisos
    if current_user.role != UserRole.ADMIN and pqrs.assigned_to_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para responder esta PQRS"
        )
    
    pqrs.respuesta = response_data.respuesta
    pqrs.estado = EstadoPQRS.RESUELTO
    pqrs.fecha_respuesta = datetime.utcnow()
    
    db.commit()
    db.refresh(pqrs)
    
    return pqrs

@router.delete("/{pqrs_id}")
async def delete_pqrs(
    pqrs_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Eliminar PQRS (solo admin)"""
    pqrs = db.query(PQRS).filter(PQRS.id == pqrs_id).first()
    
    if not pqrs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PQRS no encontrada"
        )
    
    db.delete(pqrs)
    db.commit()
    
    return {"message": "PQRS eliminada exitosamente"}