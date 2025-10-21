from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.config.database import engine, get_db, Base
from app.config.settings import settings
from app.routes import auth, pqrs, users, planes
from app.models import user, pqrs as pqrs_model, plan
from app.models.user import User, UserRole
from app.utils.auth import get_password_hash

# Crear las tablas en la base de datos
Base.metadata.create_all(bind=engine)

# Compatibilidad: añadir columna `is_active` a la tabla users en SQLite si no existe
from sqlalchemy import inspect, text
inspector = inspect(engine)
if inspector.has_table("users"):
    cols = [c.get("name") for c in inspector.get_columns("users")]
    if "is_active" not in cols:
        # Solo para SQLite añadimos la columna con default 1
        try:
            with engine.connect() as conn:
                conn.execute(text('ALTER TABLE users ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT 1'))
                conn.commit()
                print("Columna 'is_active' agregada a la tabla users")
        except Exception as e:
            print(f"No se pudo agregar la columna is_active automáticamente: {e}")

app = FastAPI(
    title="Sistema PQRS Alcaldía",
    description="API para gestión de Peticiones, Quejas, Reclamos y Sugerencias",
    version="1.0.0"
)

# Configurar CORS dinámicamente según entorno
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # URLs permitidas desde settings
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(auth.router, prefix="/api")
app.include_router(pqrs.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(planes.router, prefix="/api/planes", tags=["Planes Institucionales"])

@app.get("/")
async def root():
    return {"message": "Sistema PQRS Alcaldía API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Crear usuario administrador por defecto si no existe
@app.on_event("startup")
async def create_default_admin():
    import time
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            db = next(get_db())
            try:
                # Verificar si ya existe un admin
                admin_exists = db.query(User).filter(User.role == UserRole.ADMIN).first()
                
                if not admin_exists:
                    # Crear usuario administrador por defecto
                    password = "admin123"
                    hashed_password = get_password_hash(password)
                    
                    admin_user = User(
                        username="admin",
                        email="admin@alcaldia.gov.co",
                        full_name="Administrador del Sistema",
                        hashed_password=hashed_password,
                        role=UserRole.ADMIN,
                        secretaria="Sistemas"
                    )
                    
                    db.add(admin_user)
                    db.commit()
                    print(f"Usuario administrador creado: admin / {password}")
                    print(f"Hash generado correctamente: {hashed_password[:20]}...")
                else:
                    print("Usuario administrador ya existe")
                
                break  # Éxito, salir del loop de reintentos
                
            except Exception as e:
                db.rollback()
                if attempt < max_retries - 1:
                    print(f"Intento {attempt + 1} fallido creando usuario administrador: {e}")
                    print(f"Reintentando en {retry_delay} segundos...")
                    time.sleep(retry_delay)
                else:
                    print(f"Error creando usuario administrador después de {max_retries} intentos: {e}")
            finally:
                db.close()
                
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Error de conexión en intento {attempt + 1}: {e}")
                time.sleep(retry_delay)
            else:
                print(f"No se pudo conectar a la base de datos después de {max_retries} intentos: {e}")