from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.config.database import engine, get_db, Base
from app.config.settings import settings
from app.routes import auth, pqrs, users, planes, entities
from app.models import user, pqrs as pqrs_model, plan, entity
from app.models.user import User, UserRole
from app.utils.auth import get_password_hash

# Crear las tablas en la base de datos (solo si no existen)
Base.metadata.create_all(bind=engine)

# Compatibilidad: añadir columna `is_active` a la tabla users en SQLite si no existe
from sqlalchemy import inspect, text
inspector = inspect(engine)
if inspector.has_table("users"):
    cols = [c.get("name") for c in inspector.get_columns("users")]
    if "is_active" not in cols:
        try:
            with engine.connect() as conn:
                conn.execute(text('ALTER TABLE users ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT 1'))
                conn.commit()
        except Exception:
            pass  # Columna ya existe o error ignorado

# Nota: se removieron migraciones automáticas específicas de SQLite

# Migración automática para PostgreSQL: agregar columnas de ciudadano y PQRS
# Nota: se removieron migraciones automáticas específicas de PostgreSQL

app = FastAPI(
    title="Sistema PQRS Alcaldía",
    description="API para gestión de Peticiones, Quejas, Reclamos y Sugerencias",
    version="1.0.0"
)

# Nota: se removieron prints de CORS para un arranque limpio

# Configurar CORS dinámicamente según entorno
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # URLs permitidas desde settings
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Middleware para manejar excepciones y asegurar CORS headers
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import traceback

@app.middleware("http")
async def catch_exceptions_middleware(request: Request, call_next):
    """Middleware para capturar todas las excepciones y enviar headers CORS"""
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        # Log detallado del error
        print(f"\n❌ Error no manejado:")
        print(f"   Path: {request.method} {request.url.path}")
        print(f"   Error: {str(e)}")
        print(f"   Traceback:\n{traceback.format_exc()}")
        
        # Crear respuesta con CORS headers
        origin = request.headers.get("origin")
        if origin in settings.cors_origins or "*" in settings.cors_origins:
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Error interno del servidor",
                    "error": str(e) if settings.debug else "Internal server error"
                },
                headers={
                    "Access-Control-Allow-Origin": origin or "*",
                    "Access-Control-Allow-Credentials": "true",
                    "Access-Control-Allow-Methods": "*",
                    "Access-Control-Allow-Headers": "*",
                }
            )
        return JSONResponse(
            status_code=500,
            content={"detail": "Error interno del servidor"}
        )

# Incluir routers
app.include_router(auth.router, prefix="/api")
app.include_router(pqrs.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(planes.router, prefix="/api/planes", tags=["Planes Institucionales"])
app.include_router(entities.router, prefix="/api", tags=["Entidades"])
# Router de mantenimiento eliminado para despliegue limpio

@app.get("/")
async def root():
    return {"message": "Sistema PQRS Alcaldía API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Seed en startup eliminado; usar endpoint /api/auth/init-superadmin si se necesita