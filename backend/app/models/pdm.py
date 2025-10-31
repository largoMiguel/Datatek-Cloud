from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Float, UniqueConstraint, ForeignKey
from sqlalchemy.orm import relationship
from app.config.database import Base


class PdmMetaAssignment(Base):
    __tablename__ = "pdm_meta_assignments"

    id = Column(Integer, primary_key=True, index=True)
    entity_id = Column(Integer, ForeignKey("entities.id"), nullable=False, index=True)
    codigo_indicador_producto = Column(String(128), nullable=False, index=True)
    secretaria = Column(String(256), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("entity_id", "codigo_indicador_producto", name="uq_meta_assignment_entity_codigo"),
    )


class PdmAvance(Base):
    __tablename__ = "pdm_avances"

    id = Column(Integer, primary_key=True, index=True)
    entity_id = Column(Integer, ForeignKey("entities.id"), nullable=False, index=True)
    codigo_indicador_producto = Column(String(128), nullable=False, index=True)
    anio = Column(Integer, nullable=False)
    valor_ejecutado = Column(Float, nullable=False, default=0.0)
    comentario = Column(String(512), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("entity_id", "codigo_indicador_producto", "anio", name="uq_avance_entity_codigo_anio"),
    )


class PdmActividad(Base):
    __tablename__ = "pdm_actividades"

    id = Column(Integer, primary_key=True, index=True)
    entity_id = Column(Integer, ForeignKey("entities.id"), nullable=False, index=True)
    codigo_indicador_producto = Column(String(128), nullable=False, index=True)
    nombre = Column(String(512), nullable=False)
    descripcion = Column(String(1024), nullable=True)
    responsable = Column(String(256), nullable=True)
    fecha_inicio = Column(DateTime, nullable=True)
    fecha_fin = Column(DateTime, nullable=True)
    # Campos antiguos (compatibilidad)
    porcentaje_avance = Column(Float, nullable=False, default=0.0)
    # Nuevos campos para ejecutar por año
    anio = Column(Integer, nullable=True)
    meta_ejecutar = Column(Float, nullable=False, default=0.0)
    valor_ejecutado = Column(Float, nullable=False, default=0.0)
    estado = Column(String(64), nullable=False, default='pendiente')  # pendiente, en_progreso, completada, cancelada

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("entity_id", "codigo_indicador_producto", "nombre", name="uq_actividad_entity_codigo_nombre"),
    )
