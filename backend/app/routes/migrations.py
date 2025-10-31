"""
Endpoint de migración para actualizar base de datos en producción

IMPORTANTE: Esta migración incluye:
- Tablas PDM (pdm_meta_assignments, pdm_avances)
- Flag enable_pdm en entities
- Campos NIT y enable_contratacion
- Permisos modulares (user_type, allowed_modules)

Ejecutar:
    curl -X POST https://<backend>/api/migrations/run -H "X-Migration-Key: <CLAVE>"
    
Verificar estado:
    curl -X GET https://<backend>/api/migrations/status -H "X-Migration-Key: <CLAVE>"
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy import inspect as sa_inspect
from app.config.database import get_db
from app.config.settings import settings
import logging

router = APIRouter(prefix="/migrations", tags=["migrations"])
logger = logging.getLogger(__name__)

# Clave secreta de migración (debe estar en variable de entorno)
MIGRATION_KEY = getattr(settings, 'migration_secret_key', "change-me-in-production")


def verify_migration_key(x_migration_key: str = Header(None)):
    """Verifica la clave de migración"""
    if not x_migration_key or x_migration_key != MIGRATION_KEY:
        raise HTTPException(status_code=403, detail="Clave de migración inválida")
    return True


@router.post("/run")
def run_migrations(
    db: Session = Depends(get_db),
    authorized: bool = Depends(verify_migration_key)
):
    """
    Ejecuta las migraciones pendientes relacionadas con:
    - Campo NIT en entities (para consultas SECOP II)
    - Flag enable_contratacion en entities
    - Permisos modulares: user_type y allowed_modules en users
    """
    try:
        migrations_applied = []

        # Verificar conexión
        db.execute(text("SELECT 1"))
        migrations_applied.append("✅ Conexión a base de datos verificada")

        # Inspeccionar esquema actual
        bind = db.get_bind()
        inspector = sa_inspect(bind)
        if not inspector.has_table("entities"):
            raise HTTPException(status_code=500, detail="La tabla 'entities' no existe. Ejecuta migraciones base primero.")

        existing_cols = {c["name"] for c in inspector.get_columns("entities")}
        is_postgres = bind.dialect.name.startswith("postgres")

        # 1) Agregar columna 'nit' si falta
        if "nit" not in existing_cols:
            if is_postgres:
                db.execute(text("ALTER TABLE entities ADD COLUMN IF NOT EXISTS nit VARCHAR(50)"))
                db.execute(text("CREATE INDEX IF NOT EXISTS ix_entities_nit ON entities (nit)"))
            else:
                # SQLite y otros: agregar columna e índice si no existen
                db.execute(text("ALTER TABLE entities ADD COLUMN nit VARCHAR(50)"))
                db.execute(text("CREATE INDEX IF NOT EXISTS ix_entities_nit ON entities (nit)"))
            migrations_applied.append("🆕 Agregada columna 'nit' en entities y creado índice")
        else:
            migrations_applied.append("ℹ️ Columna 'nit' ya existe en entities")

        # 2) Agregar flag 'enable_contratacion' si falta
        if "enable_contratacion" not in existing_cols:
            default_true = "TRUE" if is_postgres else "1"
            db.execute(text(f"ALTER TABLE entities ADD COLUMN enable_contratacion BOOLEAN NOT NULL DEFAULT {default_true}"))
            # Backfill explícito para filas existentes en algunos motores
            db.execute(text(f"UPDATE entities SET enable_contratacion = {default_true} WHERE enable_contratacion IS NULL"))
            migrations_applied.append("🆕 Agregada columna 'enable_contratacion' con valor por defecto TRUE")
        else:
            migrations_applied.append("ℹ️ Columna 'enable_contratacion' ya existe en entities")

        # ====== MIGRACIONES PARA PDM (Plan de Desarrollo Municipal) ======
        
        # 3) Crear tabla pdm_meta_assignments si no existe
        if not inspector.has_table("pdm_meta_assignments"):
            if is_postgres:
                db.execute(text("""
                    CREATE TABLE pdm_meta_assignments (
                        id SERIAL PRIMARY KEY,
                        entity_id INTEGER NOT NULL REFERENCES entities(id),
                        codigo_indicador_producto VARCHAR(128) NOT NULL,
                        secretaria VARCHAR(256),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        CONSTRAINT uq_meta_assignment_entity_codigo UNIQUE (entity_id, codigo_indicador_producto)
                    )
                """))
                db.execute(text("CREATE INDEX ix_pdm_meta_assignments_entity_id ON pdm_meta_assignments(entity_id)"))
                db.execute(text("CREATE INDEX ix_pdm_meta_assignments_codigo ON pdm_meta_assignments(codigo_indicador_producto)"))
            else:
                db.execute(text("""
                    CREATE TABLE pdm_meta_assignments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        entity_id INTEGER NOT NULL,
                        codigo_indicador_producto VARCHAR(128) NOT NULL,
                        secretaria VARCHAR(256),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (entity_id) REFERENCES entities(id),
                        UNIQUE(entity_id, codigo_indicador_producto)
                    )
                """))
                db.execute(text("CREATE INDEX ix_pdm_meta_assignments_entity_id ON pdm_meta_assignments(entity_id)"))
                db.execute(text("CREATE INDEX ix_pdm_meta_assignments_codigo ON pdm_meta_assignments(codigo_indicador_producto)"))
            migrations_applied.append("🆕 Tabla 'pdm_meta_assignments' creada para asignación de metas a secretarías")
        else:
            migrations_applied.append("ℹ️ Tabla 'pdm_meta_assignments' ya existe")

        # 4) Crear tabla pdm_avances si no existe
        if not inspector.has_table("pdm_avances"):
            if is_postgres:
                db.execute(text("""
                    CREATE TABLE pdm_avances (
                        id SERIAL PRIMARY KEY,
                        entity_id INTEGER NOT NULL REFERENCES entities(id),
                        codigo_indicador_producto VARCHAR(128) NOT NULL,
                        anio INTEGER NOT NULL,
                        valor_ejecutado FLOAT NOT NULL DEFAULT 0.0,
                        comentario VARCHAR(512),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        CONSTRAINT uq_avance_entity_codigo_anio UNIQUE (entity_id, codigo_indicador_producto, anio)
                    )
                """))
                db.execute(text("CREATE INDEX ix_pdm_avances_entity_id ON pdm_avances(entity_id)"))
                db.execute(text("CREATE INDEX ix_pdm_avances_codigo ON pdm_avances(codigo_indicador_producto)"))
            else:
                db.execute(text("""
                    CREATE TABLE pdm_avances (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        entity_id INTEGER NOT NULL,
                        codigo_indicador_producto VARCHAR(128) NOT NULL,
                        anio INTEGER NOT NULL,
                        valor_ejecutado REAL NOT NULL DEFAULT 0.0,
                        comentario VARCHAR(512),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (entity_id) REFERENCES entities(id),
                        UNIQUE(entity_id, codigo_indicador_producto, anio)
                    )
                """))
                db.execute(text("CREATE INDEX ix_pdm_avances_entity_id ON pdm_avances(entity_id)"))
                db.execute(text("CREATE INDEX ix_pdm_avances_codigo ON pdm_avances(codigo_indicador_producto)"))
            migrations_applied.append("🆕 Tabla 'pdm_avances' creada para registro de avances por año")
        else:
            migrations_applied.append("ℹ️ Tabla 'pdm_avances' ya existe")

        # 4.1) Crear tabla pdm_actividades si no existe
        if not inspector.has_table("pdm_actividades"):
            if is_postgres:
                db.execute(text("""
                    CREATE TABLE pdm_actividades (
                        id SERIAL PRIMARY KEY,
                        entity_id INTEGER NOT NULL REFERENCES entities(id),
                        codigo_indicador_producto VARCHAR(128) NOT NULL,
                        nombre VARCHAR(512) NOT NULL,
                        descripcion VARCHAR(1024),
                        responsable VARCHAR(256),
                        fecha_inicio TIMESTAMP NULL,
                        fecha_fin TIMESTAMP NULL,
                        porcentaje_avance FLOAT NOT NULL DEFAULT 0.0,
                        estado VARCHAR(64) NOT NULL DEFAULT 'pendiente',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        CONSTRAINT uq_actividad_entity_codigo_nombre UNIQUE (entity_id, codigo_indicador_producto, nombre)
                    )
                """))
                db.execute(text("CREATE INDEX ix_pdm_actividades_entity_id ON pdm_actividades(entity_id)"))
                db.execute(text("CREATE INDEX ix_pdm_actividades_codigo ON pdm_actividades(codigo_indicador_producto)"))
            else:
                db.execute(text("""
                    CREATE TABLE pdm_actividades (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        entity_id INTEGER NOT NULL,
                        codigo_indicador_producto VARCHAR(128) NOT NULL,
                        nombre VARCHAR(512) NOT NULL,
                        descripcion VARCHAR(1024),
                        responsable VARCHAR(256),
                        fecha_inicio TIMESTAMP NULL,
                        fecha_fin TIMESTAMP NULL,
                        porcentaje_avance REAL NOT NULL DEFAULT 0.0,
                        estado VARCHAR(64) NOT NULL DEFAULT 'pendiente',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (entity_id) REFERENCES entities(id),
                        UNIQUE(entity_id, codigo_indicador_producto, nombre)
                    )
                """))
                db.execute(text("CREATE INDEX ix_pdm_actividades_entity_id ON pdm_actividades(entity_id)"))
                db.execute(text("CREATE INDEX ix_pdm_actividades_codigo ON pdm_actividades(codigo_indicador_producto)"))
            migrations_applied.append("🆕 Tabla 'pdm_actividades' creada para gestionar actividades por producto")
        else:
            migrations_applied.append("ℹ️ Tabla 'pdm_actividades' ya existe")

        # 4.2) Agregar columnas nuevas a pdm_actividades si faltan: anio, meta_ejecutar, valor_ejecutado
        if inspector.has_table("pdm_actividades"):
            act_cols = {c["name"] for c in inspector.get_columns("pdm_actividades")}
            if "anio" not in act_cols:
                if is_postgres:
                    db.execute(text("ALTER TABLE pdm_actividades ADD COLUMN IF NOT EXISTS anio INTEGER"))
                else:
                    db.execute(text("ALTER TABLE pdm_actividades ADD COLUMN anio INTEGER"))
                migrations_applied.append("🆕 Agregada columna 'anio' en pdm_actividades")
            else:
                migrations_applied.append("ℹ️ Columna 'anio' ya existe en pdm_actividades")

            if "meta_ejecutar" not in act_cols:
                if is_postgres:
                    db.execute(text("ALTER TABLE pdm_actividades ADD COLUMN IF NOT EXISTS meta_ejecutar FLOAT NOT NULL DEFAULT 0.0"))
                else:
                    db.execute(text("ALTER TABLE pdm_actividades ADD COLUMN meta_ejecutar REAL NOT NULL DEFAULT 0.0"))
                migrations_applied.append("🆕 Agregada columna 'meta_ejecutar' en pdm_actividades")
            else:
                migrations_applied.append("ℹ️ Columna 'meta_ejecutar' ya existe en pdm_actividades")

            if "valor_ejecutado" not in act_cols:
                if is_postgres:
                    db.execute(text("ALTER TABLE pdm_actividades ADD COLUMN IF NOT EXISTS valor_ejecutado FLOAT NOT NULL DEFAULT 0.0"))
                else:
                    db.execute(text("ALTER TABLE pdm_actividades ADD COLUMN valor_ejecutado REAL NOT NULL DEFAULT 0.0"))
                migrations_applied.append("🆕 Agregada columna 'valor_ejecutado' en pdm_actividades")
            else:
                migrations_applied.append("ℹ️ Columna 'valor_ejecutado' ya existe en pdm_actividades")

        # 5) Agregar flag 'enable_pdm' si falta en entities
        if "enable_pdm" not in existing_cols:
            default_true = "TRUE" if is_postgres else "1"
            db.execute(text(f"ALTER TABLE entities ADD COLUMN enable_pdm BOOLEAN NOT NULL DEFAULT {default_true}"))
            db.execute(text(f"UPDATE entities SET enable_pdm = {default_true} WHERE enable_pdm IS NULL"))
            migrations_applied.append("🆕 Agregada columna 'enable_pdm' con valor por defecto TRUE en entities")
        else:
            migrations_applied.append("ℹ️ Columna 'enable_pdm' ya existe en entities")

        # ====== MIGRACIONES PARA PERMISOS MODULARES ======
        
        # Verificar que exista la tabla users
        if not inspector.has_table("users"):
            raise HTTPException(status_code=500, detail="La tabla 'users' no existe. Ejecuta migraciones base primero.")

        users_cols = {c["name"] for c in inspector.get_columns("users")}

        # 6) Agregar columna 'user_type' si falta
        if "user_type" not in users_cols:
            if is_postgres:
                # Crear ENUM type si no existe
                db.execute(text("""
                    DO $$ BEGIN
                        CREATE TYPE usertype AS ENUM ('secretario', 'contratista');
                    EXCEPTION
                        WHEN duplicate_object THEN null;
                    END $$;
                """))
                db.execute(text("ALTER TABLE users ADD COLUMN user_type usertype"))
            else:
                # SQLite: usar VARCHAR
                db.execute(text("ALTER TABLE users ADD COLUMN user_type VARCHAR(20)"))
            migrations_applied.append("🆕 Agregada columna 'user_type' en users (secretario/contratista)")
        else:
            migrations_applied.append("ℹ️ Columna 'user_type' ya existe en users")

        # 7) Agregar columna 'allowed_modules' si falta
        if "allowed_modules" not in users_cols:
            if is_postgres:
                # PostgreSQL: usar JSON o JSONB
                db.execute(text("ALTER TABLE users ADD COLUMN allowed_modules JSON"))
            else:
                # SQLite: usar TEXT para almacenar JSON
                db.execute(text("ALTER TABLE users ADD COLUMN allowed_modules TEXT"))
            migrations_applied.append("🆕 Agregada columna 'allowed_modules' en users (array JSON de módulos)")
        else:
            migrations_applied.append("ℹ️ Columna 'allowed_modules' ya existe en users")

        # 8) Normalizar valores existentes de user_type (MAYÚSCULAS -> minúsculas)
        if "user_type" in users_cols:
            try:
                # Intentar contar registros a normalizar (puede fallar si ya es enum)
                if not is_postgres:
                    # En SQLite podemos hacer directamente la comparación de strings
                    count_result = db.execute(text("""
                        SELECT COUNT(*) 
                        FROM users 
                        WHERE user_type IN ('SECRETARIO', 'CONTRATISTA')
                    """))
                    count = count_result.scalar()
                    
                    if count and count > 0:
                        # Actualizar SECRETARIO -> secretario
                        db.execute(text("""
                            UPDATE users 
                            SET user_type = 'secretario' 
                            WHERE user_type = 'SECRETARIO'
                        """))
                        
                        # Actualizar CONTRATISTA -> contratista
                        db.execute(text("""
                            UPDATE users 
                            SET user_type = 'contratista' 
                            WHERE user_type = 'CONTRATISTA'
                        """))
                        
                        migrations_applied.append(f"🔧 Normalizados {count} registros: user_type a minúsculas")
                    else:
                        migrations_applied.append("ℹ️ Valores de user_type ya están normalizados")
                else:
                    # En PostgreSQL, si la columna ya es enum, no intentar normalizar
                    # porque el enum ya solo acepta valores en minúsculas
                    migrations_applied.append("ℹ️ PostgreSQL: user_type es enum, valores ya restringidos a minúsculas")
            except Exception as norm_error:
                # Si falla (porque ya es enum), simplemente continuar
                migrations_applied.append(f"ℹ️ Normalización de user_type omitida (columna ya correcta): {str(norm_error)[:100]}")

        # Commit de cambios
        db.commit()

        logger.info("Migraciones ejecutadas exitosamente")
        return {
            "status": "success",
            "message": "Migraciones ejecutadas correctamente",
            "migrations": migrations_applied,
            "details": "Migraciones aplicadas: NIT, enable_contratacion, tablas PDM (meta_assignments, avances), enable_pdm, user_type y allowed_modules (si estaban pendientes)."
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error ejecutando migraciones: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error ejecutando migraciones: {str(e)}"
        )


@router.get("/status")
def migration_status(
    db: Session = Depends(get_db),
    authorized: bool = Depends(verify_migration_key)
):
    """
    Verifica el estado de las migraciones y la base de datos
    """
    try:
        status_info = {
            "database_connection": "✅ Conectado",
            "pending_migrations": [],
            "last_migration": "PDM (Plan de Desarrollo Municipal) y Permisos modulares",
            "notes": [
                "El módulo PDM gestiona metas, asignaciones a secretarías y avances por año",
                "Tablas: pdm_meta_assignments, pdm_avances",
                "'enable_pdm' controla la visibilidad del módulo PDM",
                "El módulo de Contratación usa SECOP II (API externa)",
                "Se requiere el campo 'nit' en entities para consultar por NIT",
                "'enable_contratacion' controla la visibilidad del módulo",
                "Permisos modulares: asignar módulos específicos por usuario (secretario/contratista)"
            ]
        }

        bind = db.get_bind()
        inspector = sa_inspect(bind)
        if not inspector.has_table("entities"):
            status_info["database_connection"] = "⚠️ Sin tabla 'entities'"
            status_info["pending_migrations"].append("create_entities_table")
            return status_info

        cols = {c["name"] for c in inspector.get_columns("entities")}

        # Comprobar 'nit'
        if "nit" in cols:
            status_info["nit_field"] = "✅ Campo 'nit' existe en tabla entities"
        else:
            status_info["nit_field"] = "⚠️ Campo 'nit' no encontrado - se requiere migración"
            status_info["pending_migrations"].append("add_nit_column")

        # Comprobar 'enable_contratacion'
        if "enable_contratacion" in cols:
            status_info["enable_contratacion_field"] = "✅ Campo 'enable_contratacion' existe en entities"
        else:
            status_info["enable_contratacion_field"] = "⚠️ Campo 'enable_contratacion' no encontrado - se requiere migración"
            status_info["pending_migrations"].append("add_enable_contratacion_flag")

        # Comprobar 'enable_pdm'
        if "enable_pdm" in cols:
            status_info["enable_pdm_field"] = "✅ Campo 'enable_pdm' existe en entities"
        else:
            status_info["enable_pdm_field"] = "⚠️ Campo 'enable_pdm' no encontrado - se requiere migración"
            status_info["pending_migrations"].append("add_enable_pdm_flag")

        # Comprobar tablas PDM
        if inspector.has_table("pdm_meta_assignments"):
            status_info["pdm_meta_assignments_table"] = "✅ Tabla 'pdm_meta_assignments' existe"
        else:
            status_info["pdm_meta_assignments_table"] = "⚠️ Tabla 'pdm_meta_assignments' no encontrada - se requiere migración"
            status_info["pending_migrations"].append("create_pdm_meta_assignments_table")

        if inspector.has_table("pdm_avances"):
            status_info["pdm_avances_table"] = "✅ Tabla 'pdm_avances' existe"
        else:
            status_info["pdm_avances_table"] = "⚠️ Tabla 'pdm_avances' no encontrada - se requiere migración"
            status_info["pending_migrations"].append("create_pdm_avances_table")

        # Comprobar tabla PDM Actividades
        if inspector.has_table("pdm_actividades"):
            status_info["pdm_actividades_table"] = "✅ Tabla 'pdm_actividades' existe"
        else:
            status_info["pdm_actividades_table"] = "⚠️ Tabla 'pdm_actividades' no encontrada - se requiere migración"
            status_info["pending_migrations"].append("create_pdm_actividades_table")

        # Comprobar tabla users
        if inspector.has_table("users"):
            users_cols = {c["name"] for c in inspector.get_columns("users")}
            
            # Comprobar 'user_type'
            if "user_type" in users_cols:
                status_info["user_type_field"] = "✅ Campo 'user_type' existe en tabla users"
            else:
                status_info["user_type_field"] = "⚠️ Campo 'user_type' no encontrado - se requiere migración"
                status_info["pending_migrations"].append("add_user_type_column")

            # Comprobar 'allowed_modules'
            if "allowed_modules" in users_cols:
                status_info["allowed_modules_field"] = "✅ Campo 'allowed_modules' existe en tabla users"
            else:
                status_info["allowed_modules_field"] = "⚠️ Campo 'allowed_modules' no encontrado - se requiere migración"
                status_info["pending_migrations"].append("add_allowed_modules_column")
        else:
            status_info["users_table"] = "⚠️ Tabla 'users' no encontrada"
            status_info["pending_migrations"].append("create_users_table")

        return status_info

    except Exception as e:
        logger.error(f"Error verificando estado: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error verificando estado: {str(e)}"
        )
