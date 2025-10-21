from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.config.database import Base
import enum

class TipoSolicitud(enum.Enum):
    PETICION = "peticion"
    QUEJA = "queja"
    RECLAMO = "reclamo"
    SUGERENCIA = "sugerencia"

class EstadoPQRS(enum.Enum):
    PENDIENTE = "pendiente"
    EN_PROCESO = "en_proceso"
    RESUELTO = "resuelto"
    CERRADO = "cerrado"

class PQRS(Base):
    __tablename__ = "pqrs"
    
    id = Column(Integer, primary_key=True, index=True)
    numero_radicado = Column(String, unique=True, index=True, nullable=False)
    
    # Información del ciudadano
    nombre_ciudadano = Column(String, nullable=False)
    cedula_ciudadano = Column(String, nullable=False)
    telefono_ciudadano = Column(String, nullable=True)
    email_ciudadano = Column(String, nullable=True)
    direccion_ciudadano = Column(String, nullable=True)
    
    # Información de la PQRS
    tipo_solicitud = Column(Enum(TipoSolicitud), nullable=False)
    asunto = Column(String, nullable=False)
    descripcion = Column(Text, nullable=False)
    estado = Column(Enum(EstadoPQRS), nullable=False, default=EstadoPQRS.PENDIENTE)
    
    # Fechas importantes
    fecha_solicitud = Column(DateTime(timezone=True), server_default=func.now())
    fecha_cierre = Column(DateTime(timezone=True), nullable=True)
    fecha_delegacion = Column(DateTime(timezone=True), nullable=True)
    fecha_respuesta = Column(DateTime(timezone=True), nullable=True)
    
    # Relaciones con usuarios
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_to_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Respuesta
    respuesta = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    created_by = relationship("User", foreign_keys=[created_by_id], back_populates="pqrs_creadas")
    assigned_to = relationship("User", foreign_keys=[assigned_to_id], back_populates="pqrs_asignadas")