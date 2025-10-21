from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.config.database import get_db
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.utils.auth import get_password_hash, get_current_user

router = APIRouter()

@router.get("/users/", response_model=List[UserResponse])
async def get_users(
    role: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtener lista de usuarios.
    - Administradores pueden ver todos los usuarios
    - Secretarios pueden ver solo otros secretarios (para asignación de PQRS y colaboración)
    - Se puede filtrar por rol usando query parameter ?role=secretario
    """
    query = db.query(User)
    
    # Si es secretario, solo puede ver otros secretarios
    if current_user.role == UserRole.SECRETARIO:
        query = query.filter(User.role == UserRole.SECRETARIO)
    
    # Si es admin y se especifica un rol, filtrar por ese rol
    if current_user.role == UserRole.ADMIN and role:
        if role.lower() == "secretario":
            query = query.filter(User.role == UserRole.SECRETARIO)
        elif role.lower() == "admin":
            query = query.filter(User.role == UserRole.ADMIN)
    
    users = query.all()
    return users

@router.get("/users/{user_id}/", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtener un usuario específico por ID.
    """
    # Verificar que el usuario actual sea administrador o esté consultando su propio perfil
    if current_user.role != UserRole.ADMIN and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="No tienes permisos para acceder a esta información")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    return user

@router.post("/users/", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Crear un nuevo usuario.
    Solo administradores pueden crear usuarios.
    """
    # Verificar que el usuario actual sea administrador
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="No tienes permisos para crear usuarios")
    
    # Verificar si el username ya existe
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="El nombre de usuario ya existe")
    
    # Verificar si el email ya existe
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="El email ya está en uso")
    
    # Crear el hash de la contraseña
    hashed_password = get_password_hash(user_data.password)
    
    # Crear el usuario
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hashed_password,
        role=user_data.role,
        secretaria=user_data.secretaria,
        is_active=True
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

@router.put("/users/{user_id}/", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Actualizar un usuario existente.
    """
    # Verificar que el usuario actual sea administrador o esté actualizando su propio perfil
    if current_user.role != UserRole.ADMIN and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="No tienes permisos para actualizar este usuario")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Actualizar campos si se proporcionan
    update_data = user_data.dict(exclude_unset=True)
    
    # Si se proporciona una nueva contraseña, hashearla
    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    
    # Verificar si el username ya existe (si se está cambiando)
    if "username" in update_data and update_data["username"] != user.username:
        existing_user = db.query(User).filter(User.username == update_data["username"]).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="El nombre de usuario ya existe")
    
    # Verificar si el email ya existe (si se está cambiando)
    if "email" in update_data and update_data["email"] != user.email:
        existing_email = db.query(User).filter(User.email == update_data["email"]).first()
        if existing_email:
            raise HTTPException(status_code=400, detail="El email ya está en uso")
    
    # Aplicar las actualizaciones
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    
    return user

@router.delete("/users/{user_id}/")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Eliminar un usuario.
    Solo administradores pueden eliminar usuarios.
    """
    # Verificar que el usuario actual sea administrador
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="No tienes permisos para eliminar usuarios")
    
    # No permitir que el admin se elimine a sí mismo
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="No puedes eliminarte a ti mismo")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    db.delete(user)
    db.commit()
    
    return {"message": "Usuario eliminado exitosamente"}

@router.patch("/users/{user_id}/toggle-status/", response_model=UserResponse)
async def toggle_user_status(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Activar/desactivar un usuario.
    Solo administradores pueden cambiar el estado de usuarios.
    """
    # Verificar que el usuario actual sea administrador
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="No tienes permisos para cambiar el estado de usuarios")
    
    # No permitir que el admin se desactive a sí mismo
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="No puedes cambiar tu propio estado")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Cambiar el estado
    user.is_active = not user.is_active
    
    db.commit()
    db.refresh(user)
    
    return user