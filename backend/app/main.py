from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi import Request
from fastapi.responses import JSONResponse
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

# Compatibilidad SQLite: asegurarse de que la tabla pqrs tenga las columnas nuevas (tipo_identificacion, medio_respuesta, etc.)
def run_sqlite_migration():
    try:
        # Ejecutar sólo si la URL del engine es SQLite
        if 'sqlite' not in str(engine.url):
            return

        print("\n🔄 Ejecutando migración ligera para SQLite...")
        inspector_local = inspect(engine)
        if not inspector_local.has_table('pqrs'):
            print("   ⚠️  Tabla 'pqrs' no existe todavía; saltando migración SQLite")
            return

        cols = [c.get('name') for c in inspector_local.get_columns('pqrs')]
        with engine.connect() as conn:
            # Agregar columna tipo_identificacion si no existe
            if 'tipo_identificacion' not in cols:
                try:
                    conn.execute(text("ALTER TABLE pqrs ADD COLUMN tipo_identificacion TEXT DEFAULT 'personal'"))
                    conn.commit()
                    print("   ✅ Columna 'tipo_identificacion' agregada a pqrs (SQLite)")
                except Exception as e:
                    print(f"   ⚠️  No se pudo agregar tipo_identificacion: {e}")

            # Agregar columna medio_respuesta si no existe
            if 'medio_respuesta' not in cols:
                try:
                    conn.execute(text("ALTER TABLE pqrs ADD COLUMN medio_respuesta TEXT DEFAULT 'ticket'"))
                    conn.commit()
                    print("   ✅ Columna 'medio_respuesta' agregada a pqrs (SQLite)")
                except Exception as e:
                    print(f"   ⚠️  No se pudo agregar medio_respuesta: {e}")

            # Asegurar columnas opcionales (nombre_ciudadano, cedula_ciudadano, asunto) existen
            optional_cols = {
                'nombre_ciudadano': "ALTER TABLE pqrs ADD COLUMN nombre_ciudadano TEXT",
                'cedula_ciudadano': "ALTER TABLE pqrs ADD COLUMN cedula_ciudadano TEXT",
                'asunto': "ALTER TABLE pqrs ADD COLUMN asunto TEXT"
            }
            for col, sql in optional_cols.items():
                if col not in cols:
                    try:
                        conn.execute(text(sql))
                        conn.commit()
                        print(f"   ✅ Columna '{col}' agregada a pqrs (SQLite)")
                    except Exception as e:
                        print(f"   ⚠️  No se pudo agregar {col}: {e}")

        print("   ✅ Migración SQLite completada")
    except Exception as e:
        print(f"   ⚠️  Error en migración SQLite: {e}")

# Ejecutar migración SQLite (si aplica)
run_sqlite_migration()

# Migración automática para PostgreSQL: agregar columnas de ciudadano y PQRS
def run_postgres_migration():
    """Ejecuta las migraciones para agregar columnas cedula, telefono, direccion y tipo_identificacion, medio_respuesta"""
    try:
        # Detectar si es PostgreSQL
        if 'postgresql' not in str(engine.url):
            return  # Solo ejecutar en PostgreSQL
        
        print("\n🔄 Ejecutando migración de PostgreSQL...")
        
        # Paso 1: Agregar valor CIUDADANO al enum userrole si no existe
        try:
            with engine.connect() as conn:
                check_enum = text("""
                    SELECT EXISTS (
                        SELECT 1 FROM pg_enum
                        WHERE enumlabel = 'CIUDADANO'
                        AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'userrole')
                    ) as exists;
                """)
                result = conn.execute(check_enum).scalar()
                
                if not result:
                    conn.execute(text("COMMIT"))
                    conn.execute(text("ALTER TYPE userrole ADD VALUE 'CIUDADANO'"))
                    print("   ✅ Valor CIUDADANO agregado al enum userrole")
        except Exception as e:
            print(f"   ⚠️  ENUM userrole: {e}")
        
        # Paso 2: Agregar columnas a users si no existen
        user_migrations = [
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS cedula VARCHAR(20)",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS telefono VARCHAR(20)",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS direccion VARCHAR(255)",
            "CREATE INDEX IF NOT EXISTS idx_users_cedula ON users(cedula)"
        ]
        
        with engine.connect() as conn:
            for sql in user_migrations:
                try:
                    conn.execute(text(sql))
                    conn.commit()
                except Exception as e:
                    print(f"   ⚠️  {sql[:30]}...: {e}")
        
        # Paso 3: Crear ENUMs para PQRS (tipoidentificacion, mediorespuesta)
        try:
            with engine.connect() as conn:
                # Crear enum tipoidentificacion
                check_tipo = text("""
                    SELECT EXISTS (
                        SELECT 1 FROM pg_type WHERE typname = 'tipoidentificacion'
                    ) as exists;
                """)
                if not conn.execute(check_tipo).scalar():
                    conn.execute(text("CREATE TYPE tipoidentificacion AS ENUM ('personal', 'anonima')"))
                    conn.commit()
                    print("   ✅ ENUM tipoidentificacion creado")
                
                # Crear enum mediorespuesta
                check_medio = text("""
                    SELECT EXISTS (
                        SELECT 1 FROM pg_type WHERE typname = 'mediorespuesta'
                    ) as exists;
                """)
                if not conn.execute(check_medio).scalar():
                    conn.execute(text("CREATE TYPE mediorespuesta AS ENUM ('email', 'fisica', 'telefono', 'ticket')"))
                    conn.commit()
                    print("   ✅ ENUM mediorespuesta creado")
        except Exception as e:
            print(f"   ⚠️  ENUMs PQRS: {e}")
        
        # Paso 4: Agregar columnas a pqrs
        pqrs_migrations = [
            "ALTER TABLE pqrs ADD COLUMN IF NOT EXISTS tipo_identificacion tipoidentificacion DEFAULT 'personal'",
            "ALTER TABLE pqrs ADD COLUMN IF NOT EXISTS medio_respuesta mediorespuesta DEFAULT 'email'",
            "ALTER TABLE pqrs ALTER COLUMN nombre_ciudadano DROP NOT NULL",
            "ALTER TABLE pqrs ALTER COLUMN cedula_ciudadano DROP NOT NULL",
            "ALTER TABLE pqrs ALTER COLUMN asunto DROP NOT NULL"
        ]
        
        with engine.connect() as conn:
            for sql in pqrs_migrations:
                try:
                    conn.execute(text(sql))
                    conn.commit()
                except Exception as e:
                    # Ignorar error si la columna ya permite NULL
                    if "does not exist" not in str(e).lower():
                        print(f"   ⚠️  {sql[:40]}...: {e}")
        
        print("   ✅ Migración PostgreSQL completada")
        
    except Exception as e:
        print(f"   ⚠️  Error en migración: {e}")

# Ejecutar migración al importar
run_postgres_migration()

app = FastAPI(
    title="Sistema PQRS Alcaldía",
    description="API para gestión de Peticiones, Quejas, Reclamos y Sugerencias",
    version="1.0.0"
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Manejador temporal para loguear el body que causa errores 422 y devolver detalles.
    Esto ayuda a depurar por qué algunas solicitudes (p. ej. creación anónima) fallan la validación.
    """
    try:
        raw = await request.body()
        body_text = raw.decode('utf-8') if raw else ''
    except Exception:
        body_text = '<no body available>'

    # Loguear en stdout para que el desarrollador lo vea en la consola
    print('\n==== RequestValidationError detected ====')
    print('Path:', request.url.path)
    print('Body:', body_text)
    print('Errors:', exc.errors())
    print('========================================\n')

    # Devolver la respuesta 422 con los detalles y el body para debugging temporal
    return JSONResponse(status_code=422, content={"detail": exc.errors(), "body": body_text})

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
    from sqlalchemy.exc import IntegrityError
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            db = next(get_db())
            try:
                # Verificar si ya existe un admin
                admin_exists = db.query(User).filter(User.role == UserRole.ADMIN).first()
                
                if admin_exists:
                    print("Usuario administrador ya existe")
                    break
                
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
                print(f"✓ Usuario administrador creado: admin / {password}")
                break  # Éxito, salir del loop
                
            except IntegrityError as e:
                db.rollback()
                # Si es error de duplicado, el usuario ya existe (carreras de condición)
                if "duplicate key" in str(e).lower() or "unique constraint" in str(e).lower():
                    print("Usuario administrador ya existe (detectado en commit)")
                    break
                else:
                    raise  # Re-lanzar si es otro tipo de IntegrityError
                    
            except Exception as e:
                db.rollback()
                if attempt < max_retries - 1:
                    print(f"Intento {attempt + 1} fallido: {type(e).__name__}")
                    time.sleep(retry_delay)
                else:
                    print(f"Error después de {max_retries} intentos: {e}")
            finally:
                db.close()
                
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Error de conexión en intento {attempt + 1}: {type(e).__name__}")
                time.sleep(retry_delay)
            else:
                print(f"No se pudo conectar después de {max_retries} intentos: {e}")