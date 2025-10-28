from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.config.database import engine, get_db, Base
from app.config.settings import settings
from app.routes import auth, pqrs, users, planes, entities, maintenance
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

# Compatibilidad SQLite: asegurarse de que la tabla pqrs tenga las columnas nuevas
def run_sqlite_migration():
    try:
        if 'sqlite' not in str(engine.url):
            return

        inspector_local = inspect(engine)
        # Migraciones para tabla pqrs
        if inspector_local.has_table('pqrs'):
            cols = [c.get('name') for c in inspector_local.get_columns('pqrs')]
            with engine.connect() as conn:
                # Agregar columnas nuevas si no existen
                if 'tipo_identificacion' not in cols:
                    try:
                        conn.execute(text("ALTER TABLE pqrs ADD COLUMN tipo_identificacion TEXT DEFAULT 'personal'"))
                        conn.commit()
                    except Exception:
                        pass

                if 'medio_respuesta' not in cols:
                    try:
                        conn.execute(text("ALTER TABLE pqrs ADD COLUMN medio_respuesta TEXT DEFAULT 'ticket'"))
                        conn.commit()
                    except Exception:
                        pass

                # Asegurar columnas opcionales existen
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
                        except Exception:
                            pass

        # Migraciones para tabla entities (feature flags)
        if inspector_local.has_table('entities'):
            ecols = [c.get('name') for c in inspector_local.get_columns('entities')]
            with engine.connect() as conn:
                entity_flag_migrations_sqlite = {
                    'enable_pqrs': "ALTER TABLE entities ADD COLUMN enable_pqrs INTEGER NOT NULL DEFAULT 1",
                    'enable_users_admin': "ALTER TABLE entities ADD COLUMN enable_users_admin INTEGER NOT NULL DEFAULT 1",
                    'enable_reports_pdf': "ALTER TABLE entities ADD COLUMN enable_reports_pdf INTEGER NOT NULL DEFAULT 1",
                    'enable_ai_reports': "ALTER TABLE entities ADD COLUMN enable_ai_reports INTEGER NOT NULL DEFAULT 1",
                    'enable_planes_institucionales': "ALTER TABLE entities ADD COLUMN enable_planes_institucionales INTEGER NOT NULL DEFAULT 1",
                }
                for col, sql in entity_flag_migrations_sqlite.items():
                    if col not in ecols:
                        try:
                            conn.execute(text(sql))
                            conn.commit()
                        except Exception:
                            pass
    except Exception:
        pass

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
        
        # Paso 2: Agregar columnas a users si no existen (incluye entity_id)
        with engine.connect() as conn:
            user_migrations = [
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS cedula VARCHAR(20)",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS telefono VARCHAR(20)",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS direccion VARCHAR(255)",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS entity_id INTEGER",
                "CREATE INDEX IF NOT EXISTS idx_users_cedula ON users(cedula)",
            ]
            for sql in user_migrations:
                try:
                    conn.execute(text(sql))
                    conn.commit()
                except Exception as e:
                    print(f"   ⚠️  {sql[:50]}...: {e}")

            # Agregar FK users.entity_id -> entities.id si no existe
            try:
                fk_exists = conn.execute(text("""
                    SELECT 1 FROM information_schema.table_constraints 
                    WHERE table_name = 'users' AND constraint_name = 'fk_users_entity'
                """)).scalar()
                if not fk_exists:
                    conn.execute(text(
                        "ALTER TABLE users ADD CONSTRAINT fk_users_entity FOREIGN KEY (entity_id) REFERENCES entities(id) ON DELETE CASCADE"
                    ))
                    conn.commit()
            except Exception as e:
                print(f"   ⚠️  FK users.entity_id -> entities.id: {e}")
        
        # Paso 3: Crear ENUMs para PQRS (tipoidentificacion, mediorespuesta)
        # IMPORTANTE: Si el enum ya existe con valores incorrectos, necesitamos recrearlo
        try:
            with engine.connect() as conn:
                # Verificar si tipoidentificacion existe
                check_tipo = text("""
                    SELECT EXISTS (
                        SELECT 1 FROM pg_type WHERE typname = 'tipoidentificacion'
                    ) as exists;
                """)
                tipo_exists = conn.execute(check_tipo).scalar()
                
                if tipo_exists:
                    # Verificar si tiene los valores correctos
                    check_values = text("""
                        SELECT enumlabel FROM pg_enum 
                        WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'tipoidentificacion')
                        ORDER BY enumsortorder;
                    """)
                    existing_values = [row[0] for row in conn.execute(check_values).fetchall()]
                    
                    # Si los valores son incorrectos (mayúsculas), eliminar y recrear
                    if existing_values and existing_values[0].isupper():
                        print(f"   ⚠️  ENUM tipoidentificacion existe con valores incorrectos: {existing_values}")
                        print("   🔄 Eliminando y recreando ENUM tipoidentificacion...")
                        
                        # Primero eliminar la columna que usa el enum
                        try:
                            conn.execute(text("ALTER TABLE pqrs DROP COLUMN IF EXISTS tipo_identificacion CASCADE"))
                            conn.commit()
                        except Exception as e:
                            print(f"   ⚠️  Error al eliminar columna: {e}")
                            conn.rollback()
                        
                        # Eliminar el enum antiguo
                        try:
                            conn.execute(text("DROP TYPE IF EXISTS tipoidentificacion CASCADE"))
                            conn.commit()
                        except Exception as e:
                            print(f"   ⚠️  Error al eliminar enum: {e}")
                            conn.rollback()
                        
                        tipo_exists = False  # Marcar para recrear
                
                if not tipo_exists:
                    conn.execute(text("CREATE TYPE tipoidentificacion AS ENUM ('personal', 'anonima')"))
                    conn.commit()
                    print("   ✅ ENUM tipoidentificacion creado")
                
                # Similar para mediorespuesta
                check_medio = text("""
                    SELECT EXISTS (
                        SELECT 1 FROM pg_type WHERE typname = 'mediorespuesta'
                    ) as exists;
                """)
                medio_exists = conn.execute(check_medio).scalar()
                
                if medio_exists:
                    check_values = text("""
                        SELECT enumlabel FROM pg_enum 
                        WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'mediorespuesta')
                        ORDER BY enumsortorder;
                    """)
                    existing_values = [row[0] for row in conn.execute(check_values).fetchall()]
                    
                    if existing_values and existing_values[0].isupper():
                        print(f"   ⚠️  ENUM mediorespuesta existe con valores incorrectos: {existing_values}")
                        print("   🔄 Eliminando y recreando ENUM mediorespuesta...")
                        
                        try:
                            conn.execute(text("ALTER TABLE pqrs DROP COLUMN IF EXISTS medio_respuesta CASCADE"))
                            conn.commit()
                        except Exception as e:
                            print(f"   ⚠️  Error al eliminar columna: {e}")
                            conn.rollback()
                        
                        try:
                            conn.execute(text("DROP TYPE IF EXISTS mediorespuesta CASCADE"))
                            conn.commit()
                        except Exception as e:
                            print(f"   ⚠️  Error al eliminar enum: {e}")
                            conn.rollback()
                        
                        medio_exists = False
                
                if not medio_exists:
                    conn.execute(text("CREATE TYPE mediorespuesta AS ENUM ('email', 'fisica', 'telefono', 'ticket')"))
                    conn.commit()
                    print("   ✅ ENUM mediorespuesta creado")
                
                # Verificar y corregir tiposolicitud
                check_tipo_sol = text("""
                    SELECT EXISTS (
                        SELECT 1 FROM pg_type WHERE typname = 'tiposolicitud'
                    ) as exists;
                """)
                tipo_sol_exists = conn.execute(check_tipo_sol).scalar()
                
                if tipo_sol_exists:
                    check_values = text("""
                        SELECT enumlabel FROM pg_enum 
                        WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'tiposolicitud')
                        ORDER BY enumsortorder;
                    """)
                    existing_values = [row[0] for row in conn.execute(check_values).fetchall()]
                    
                    # Verificar si tiene valores incorrectos (mayúsculas)
                    if existing_values and any(v[0].isupper() for v in existing_values):
                        print(f"   ⚠️  ENUM tiposolicitud existe con valores incorrectos: {existing_values}")
                        print("   🔄 Eliminando y recreando ENUM tiposolicitud...")
                        
                        try:
                            conn.execute(text("ALTER TABLE pqrs DROP COLUMN IF EXISTS tipo_solicitud CASCADE"))
                            conn.commit()
                        except Exception as e:
                            print(f"   ⚠️  Error al eliminar columna tipo_solicitud: {e}")
                            conn.rollback()
                        
                        try:
                            conn.execute(text("DROP TYPE IF EXISTS tiposolicitud CASCADE"))
                            conn.commit()
                        except Exception as e:
                            print(f"   ⚠️  Error al eliminar enum tiposolicitud: {e}")
                            conn.rollback()
                        
                        tipo_sol_exists = False
                
                if not tipo_sol_exists:
                    conn.execute(text("CREATE TYPE tiposolicitud AS ENUM ('peticion', 'queja', 'reclamo', 'sugerencia')"))
                    conn.commit()
                    print("   ✅ ENUM tiposolicitud creado")
                
                # Verificar y corregir estadopqrs
                check_estado = text("""
                    SELECT EXISTS (
                        SELECT 1 FROM pg_type WHERE typname = 'estadopqrs'
                    ) as exists;
                """)
                estado_exists = conn.execute(check_estado).scalar()
                
                if estado_exists:
                    check_values = text("""
                        SELECT enumlabel FROM pg_enum 
                        WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'estadopqrs')
                        ORDER BY enumsortorder;
                    """)
                    existing_values = [row[0] for row in conn.execute(check_values).fetchall()]
                    
                    if existing_values and any(v[0].isupper() for v in existing_values):
                        print(f"   ⚠️  ENUM estadopqrs existe con valores incorrectos: {existing_values}")
                        print("   🔄 Eliminando y recreando ENUM estadopqrs...")
                        
                        try:
                            conn.execute(text("ALTER TABLE pqrs DROP COLUMN IF EXISTS estado CASCADE"))
                            conn.commit()
                        except Exception as e:
                            print(f"   ⚠️  Error al eliminar columna estado: {e}")
                            conn.rollback()
                        
                        try:
                            conn.execute(text("DROP TYPE IF EXISTS estadopqrs CASCADE"))
                            conn.commit()
                        except Exception as e:
                            print(f"   ⚠️  Error al eliminar enum estadopqrs: {e}")
                            conn.rollback()
                        
                        estado_exists = False
                
                if not estado_exists:
                    conn.execute(text("CREATE TYPE estadopqrs AS ENUM ('pendiente', 'en_proceso', 'resuelto', 'cerrado')"))
                    conn.commit()
                    print("   ✅ ENUM estadopqrs creado")
                    
        except Exception as e:
            print(f"   ⚠️  ENUMs PQRS: {e}")
        
        # Paso 4: Agregar columnas a pqrs (incluyendo tipo_solicitud y estado si fueron eliminados)
        pqrs_migrations = [
            "ALTER TABLE pqrs ADD COLUMN IF NOT EXISTS tipo_identificacion tipoidentificacion DEFAULT 'personal'",
            "ALTER TABLE pqrs ADD COLUMN IF NOT EXISTS medio_respuesta mediorespuesta DEFAULT 'email'",
            "ALTER TABLE pqrs ADD COLUMN IF NOT EXISTS tipo_solicitud tiposolicitud NOT NULL DEFAULT 'peticion'",
            "ALTER TABLE pqrs ADD COLUMN IF NOT EXISTS estado estadopqrs NOT NULL DEFAULT 'pendiente'",
            "ALTER TABLE pqrs ADD COLUMN IF NOT EXISTS entity_id INTEGER",
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

            # FK pqrs.entity_id -> entities.id
            try:
                fk_exists = conn.execute(text("""
                    SELECT 1 FROM information_schema.table_constraints 
                    WHERE table_name = 'pqrs' AND constraint_name = 'fk_pqrs_entity'
                """
                )).scalar()
                if not fk_exists:
                    conn.execute(text(
                        "ALTER TABLE pqrs ADD CONSTRAINT fk_pqrs_entity FOREIGN KEY (entity_id) REFERENCES entities(id) ON DELETE CASCADE"
                    ))
                    conn.commit()
            except Exception as e:
                print(f"   ⚠️  FK pqrs.entity_id -> entities.id: {e}")

        # Paso 5: Asegurar columna entity_id en planes_institucionales
        with engine.connect() as conn:
            try:
                conn.execute(text("ALTER TABLE planes_institucionales ADD COLUMN IF NOT EXISTS entity_id INTEGER"))
                conn.commit()
            except Exception as e:
                print(f"   ⚠️  planes_institucionales.entity_id: {e}")
            try:
                fk_exists = conn.execute(text("""
                    SELECT 1 FROM information_schema.table_constraints 
                    WHERE table_name = 'planes_institucionales' AND constraint_name = 'fk_planes_entity'
                """ )).scalar()
                if not fk_exists:
                    conn.execute(text(
                        "ALTER TABLE planes_institucionales ADD CONSTRAINT fk_planes_entity FOREIGN KEY (entity_id) REFERENCES entities(id) ON DELETE CASCADE"
                    ))
                    conn.commit()
            except Exception as e:
                print(f"   ⚠️  FK planes_institucionales.entity_id -> entities.id: {e}")
        
    # Paso 6: Agregar columnas de flags de características a entities (multi-modulo por entidad)
        print("   🔧 Verificando columnas de feature flags en 'entities' ...")
        entity_flag_migrations = [
            "ALTER TABLE entities ADD COLUMN IF NOT EXISTS enable_pqrs BOOLEAN NOT NULL DEFAULT TRUE",
            "ALTER TABLE entities ADD COLUMN IF NOT EXISTS enable_users_admin BOOLEAN NOT NULL DEFAULT TRUE",
            "ALTER TABLE entities ADD COLUMN IF NOT EXISTS enable_reports_pdf BOOLEAN NOT NULL DEFAULT TRUE",
            "ALTER TABLE entities ADD COLUMN IF NOT EXISTS enable_ai_reports BOOLEAN NOT NULL DEFAULT TRUE",
            "ALTER TABLE entities ADD COLUMN IF NOT EXISTS enable_planes_institucionales BOOLEAN NOT NULL DEFAULT TRUE",
        ]

        with engine.connect() as conn:
            for sql in entity_flag_migrations:
                try:
                    conn.execute(text(sql))
                    conn.commit()
                except Exception as e:
                    print(f"   ⚠️  {sql[:50]}...: {e}")

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

# Debug: imprimir orígenes CORS permitidos
print(f"\n🌐 CORS Origins configurados: {settings.cors_origins}")
print(f"   Allowed Origins String: {settings.allowed_origins}")

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
app.include_router(maintenance.router, prefix="/api/admin", tags=["Mantenimiento"]) 

@app.get("/")
async def root():
    return {"message": "Sistema PQRS Alcaldía API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

def _seed_superadmin():
    """Crea el superadmin si no existe, tomando credenciales desde settings."""
    from sqlalchemy.exc import IntegrityError
    db = next(get_db())
    try:
        sa_exists = db.query(User).filter(User.role == UserRole.SUPERADMIN).first()
        if sa_exists:
            if settings.debug:
                print("Superadmin ya existe")
            return
        username = settings.superadmin_username
        email = settings.superadmin_email
        password = settings.superadmin_password
        hashed = get_password_hash(password)
        superadmin = User(
            username=username,
            email=email,
            full_name="Super Administrador",
            hashed_password=hashed,
            role=UserRole.SUPERADMIN,
            secretaria=None,
            entity_id=None
        )
        db.add(superadmin)
        db.commit()
        if settings.debug:
            print(f"✓ Superadmin creado: {username}")
    except IntegrityError:
        db.rollback()
        if settings.debug:
            print("Superadmin ya existe (constraint)")
    finally:
        db.close()


@app.on_event("startup")
async def on_startup_seed_superadmin():
    # Sembrar superadmin únicamente
    _seed_superadmin()