from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.config.database import Base
import enum

class UserRole(enum.Enum):
    ADMIN = "admin"
    SECRETARIO = "secretario"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.SECRETARIO)
    secretaria = Column(String, nullable=True)  # Secretaría a la que pertenece
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, nullable=False, server_default="1", default=True)
    
    # Relaciones
    pqrs_creadas = relationship("PQRS", foreign_keys="PQRS.created_by_id", back_populates="created_by")
    pqrs_asignadas = relationship("PQRS", foreign_keys="PQRS.assigned_to_id", back_populates="assigned_to")