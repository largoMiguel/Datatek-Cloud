from typing import Optional, List, Dict
from pydantic import BaseModel, Field


class AssignmentBase(BaseModel):
    codigo_indicador_producto: str = Field(..., min_length=1)
    secretaria: Optional[str] = None


class AssignmentUpsertRequest(AssignmentBase):
    pass


class AssignmentResponse(AssignmentBase):
    entity_id: int

    class Config:
        from_attributes = True


class AvanceBase(BaseModel):
    codigo_indicador_producto: str
    anio: int
    valor_ejecutado: float
    comentario: Optional[str] = None


class AvanceUpsertRequest(AvanceBase):
    pass


class AvanceResponse(AvanceBase):
    entity_id: int

    class Config:
        from_attributes = True


class AssignmentsMapResponse(BaseModel):
    assignments: Dict[str, Optional[str]]


class AvancesListResponse(BaseModel):
    codigo_indicador_producto: str
    avances: List[AvanceResponse]
