from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config.settings import settings

# Configurar argumentos de conexión según el tipo de base de datos
if "sqlite" in settings.database_url:
    connect_args = {"check_same_thread": False}
else:
    # PostgreSQL - Configuración para Render y producción
    connect_args = {
        "connect_timeout": 10,
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5,
    }

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    pool_pre_ping=True,  # Verifica la conexión antes de usarla
    pool_recycle=3600,   # Recicla conexiones cada hora
    pool_size=10,        # Tamaño del pool
    max_overflow=20,     # Conexiones adicionales permitidas
    echo=False           # No mostrar SQL en logs (cambiar a True para debug)
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()