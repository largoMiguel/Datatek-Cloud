from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey, Enum as SQLEnum, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime
from app.config.database import Base
import enum

class EstadoPlan(str, enum.Enum):
    """Estados posibles para un plan institucional"""
    ACTIVO = "activo"
    FINALIZADO = "finalizado"
    SUSPENDIDO = "suspendido"

class EstadoMeta(str, enum.Enum):
    """Estados posibles para una meta"""
    NO_INICIADA = "no_iniciada"
    EN_PROGRESO = "en_progreso"
    COMPLETADA = "completada"
    ATRASADA = "atrasada"

class PlanInstitucional(Base):
    """Modelo para planes institucionales del municipio"""
    __tablename__ = "planes_institucionales"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(200), nullable=False)
    descripcion = Column(Text, nullable=False)
    anio = Column(Integer, nullable=False, index=True)
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin = Column(Date, nullable=False)
    estado = Column(SQLEnum(EstadoPlan), default=EstadoPlan.ACTIVO, nullable=False)
    
    # Relación con entidad
    entity_id = Column(Integer, ForeignKey("entities.id"), nullable=False)
    
    # Relación con metas
    metas = relationship("Meta", back_populates="plan", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<PlanInstitucional(id={self.id}, nombre='{self.nombre}', anio={self.anio})>"


class Meta(Base):
    """Modelo para metas de un plan institucional"""
    __tablename__ = "metas"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(200), nullable=False)
    descripcion = Column(Text, nullable=False)
    indicador = Column(String(200), nullable=False)
    meta_numerica = Column(Numeric(10, 2), nullable=False)
    avance_actual = Column(Numeric(10, 2), default=0, nullable=False)
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin = Column(Date, nullable=False)
    responsable = Column(String(200), nullable=False, index=True)  # Secretaría responsable
    estado = Column(SQLEnum(EstadoMeta), default=EstadoMeta.NO_INICIADA, nullable=False)
    resultado = Column(Text, nullable=True)  # Observaciones/resultados
    
    # Relación con plan
    plan_id = Column(Integer, ForeignKey("planes_institucionales.id", ondelete="CASCADE"), nullable=False)
    plan = relationship("PlanInstitucional", back_populates="metas")

    def __repr__(self):
        return f"<Meta(id={self.id}, nombre='{self.nombre}', responsable='{self.responsable}')>"
