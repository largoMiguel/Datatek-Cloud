from fastapi import APIRouter, Query, HTTPException
from typing import Optional
import httpx
from urllib.parse import urlencode

router = APIRouter(prefix="/contratacion", tags=["Contratación"])

DATOS_GOV_BASE_URL = "https://www.datos.gov.co/resource/p6dx-8zbt.json"


@router.get("/proxy")
async def proxy_datos_gov(query: Optional[str] = Query(None, alias="$query")):
    """
    Proxy para consultar el API de datos.gov.co (SECOP II).
    Evita problemas de CORS haciendo la petición desde el servidor.
    """
    try:
        params = {}
        if query:
            params["$query"] = query
        
        # Construir URL completa
        url = DATOS_GOV_BASE_URL
        if params:
            url = f"{url}?{urlencode(params)}"
        
        # Hacer petición al API externo
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            
            # Retornar la respuesta JSON
            return response.json()
            
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Error al consultar datos.gov.co: {e.response.text}"
        )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="Timeout al consultar datos.gov.co"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )
