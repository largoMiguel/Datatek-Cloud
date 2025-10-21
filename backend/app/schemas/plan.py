from pydantic import BaseModel, Field
from typing import Optional, List, TYPE_CHECKING
from datetime import date
from app.models.plan import EstadoPlan, EstadoMeta

if TYPE_CHECKING:
    pass

# ==================== SCHEMAS PARA PLAN INSTITUCIONAL ====================

class PlanInstitucionalBase(BaseModel):
    """Schema base para Plan Institucional"""
    nombre: str = Field(..., min_length=3, max_length=200)
    descripcion: str = Field(..., min_length=10)
    anio: int = Field(..., ge=2000, le=2100)
    fecha_inicio: date
    fecha_fin: date
    estado: EstadoPlan = EstadoPlan.ACTIVO


class PlanInstitucionalCreate(PlanInstitucionalBase):
    """Schema para crear un plan institucional"""
    pass


class PlanInstitucionalUpdate(BaseModel):
    """Schema para actualizar un plan institucional (todos los campos opcionales)"""
    nombre: Optional[str] = Field(None, min_length=3, max_length=200)
    descripcion: Optional[str] = Field(None, min_length=10)
    anio: Optional[int] = Field(None, ge=2000, le=2100)
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    estado: Optional[EstadoPlan] = None


class PlanInstitucional(PlanInstitucionalBase):
    """Schema para respuesta de plan institucional"""
    id: int

    class Config:
        from_attributes = True


# ==================== SCHEMAS PARA META ====================

class MetaBase(BaseModel):
    """Schema base para Meta"""
    nombre: str = Field(..., min_length=3, max_length=200)
    descripcion: str = Field(..., min_length=10)
    indicador: str = Field(..., min_length=3, max_length=200)
    meta_numerica: float = Field(..., gt=0)
    avance_actual: float = Field(default=0, ge=0)
    fecha_inicio: date
    fecha_fin: date
    responsable: str = Field(..., min_length=3, max_length=200)
    estado: EstadoMeta = EstadoMeta.NO_INICIADA
    resultado: Optional[str] = None


class MetaCreate(MetaBase):
    """Schema para crear una meta"""
    plan_id: int


class MetaUpdate(BaseModel):
    """Schema para actualizar una meta (todos los campos opcionales)"""
    nombre: Optional[str] = Field(None, min_length=3, max_length=200)
    descripcion: Optional[str] = Field(None, min_length=10)
    indicador: Optional[str] = Field(None, min_length=3, max_length=200)
    meta_numerica: Optional[float] = Field(None, gt=0)
    avance_actual: Optional[float] = Field(None, ge=0)
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    responsable: Optional[str] = Field(None, min_length=3, max_length=200)
    estado: Optional[EstadoMeta] = None
    resultado: Optional[str] = None


class Meta(MetaBase):
    """Schema para respuesta de meta"""
    id: int
    plan_id: int

    class Config:
        from_attributes = True


# Schema con metas incluidas (después de definir Meta)
class PlanInstitucionalConMetas(PlanInstitucional):
    """Schema para plan institucional con sus metas incluidas"""
    metas: List[Meta] = []

    class Config:
        from_attributes = True

