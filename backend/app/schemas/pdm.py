from typing import Optional, List, Dict
from pydantic import BaseModel, Field
from datetime import datetime


class ExcelUploadResponse(BaseModel):
    entity_id: int
    nombre_archivo: str
    tamanio: int
    created_at: datetime
    mensaje: str

    class Config:
        from_attributes = True


class ExcelInfoResponse(BaseModel):
    existe: bool
    nombre_archivo: Optional[str] = None
    tamanio: Optional[int] = None
    fecha_carga: Optional[datetime] = None

    class Config:
        from_attributes = True


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


class ActividadBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=512)
    descripcion: Optional[str] = Field(None, max_length=1024)
    responsable: Optional[str] = Field(None, max_length=256)
    fecha_inicio: Optional[str] = None  # ISO format string
    fecha_fin: Optional[str] = None  # ISO format string
    estado: str = Field(default='pendiente', max_length=64)  # pendiente, en_progreso, completada, cancelada
    # Nuevos campos de ejecución por año
    anio: int
    meta_ejecutar: float = Field(default=0.0, ge=0.0)
    valor_ejecutado: float = Field(default=0.0, ge=0.0)


class ActividadCreateRequest(ActividadBase):
    codigo_indicador_producto: str = Field(..., min_length=1)


class ActividadUpdateRequest(BaseModel):
    nombre: Optional[str] = Field(None, min_length=1, max_length=512)
    descripcion: Optional[str] = Field(None, max_length=1024)
    responsable: Optional[str] = Field(None, max_length=256)
    fecha_inicio: Optional[str] = None
    fecha_fin: Optional[str] = None
    estado: Optional[str] = Field(None, max_length=64)
    anio: Optional[int] = None
    meta_ejecutar: Optional[float] = Field(None, ge=0.0)
    valor_ejecutado: Optional[float] = Field(None, ge=0.0)


class ActividadResponse(ActividadBase):
    id: int
    entity_id: int
    codigo_indicador_producto: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class ActividadesListResponse(BaseModel):
    codigo_indicador_producto: str
    actividades: List[ActividadResponse]


# Schemas para evidencias de actividades
class EvidenciaBase(BaseModel):
    descripcion: Optional[str] = Field(None, max_length=2048)
    url: Optional[str] = Field(None, max_length=512)
    nombre_imagen: Optional[str] = Field(None, max_length=256)
    mime_type: Optional[str] = Field(None, max_length=64)
    tamano: Optional[int] = None
    contenido: Optional[str] = None  # Base64 encoded image


class EvidenciaCreateRequest(BaseModel):
    actividad_id: int
    descripcion: Optional[str] = Field(None, max_length=2048)
    url: Optional[str] = Field(None, max_length=512)
    imagenes: Optional[List[dict]] = None  # Lista de imágenes {nombre, mime_type, tamano, contenido_base64}


class EvidenciaResponse(BaseModel):
    id: int
    actividad_id: int
    entity_id: int
    descripcion: Optional[str] = None
    url: Optional[str] = None
    nombre_imagen: Optional[str] = None
    mime_type: Optional[str] = None
    tamano: Optional[int] = None
    contenido: Optional[str] = None  # Base64 encoded
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class EvidenciasListResponse(BaseModel):
    actividad_id: int
    evidencias: List[EvidenciaResponse]
