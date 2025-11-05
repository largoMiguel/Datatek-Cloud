"""
Endpoints para ejecutar y monitorear migraciones de base de datos
Uso:
- POST /api/migrations/run - Ejecuta todas las migraciones pendientes
- GET /api/migrations/status - Verifica el estado de la base de datos
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from sqlalchemy import text, inspect, Table, Column, String, Integer, Float, Date, Boolean
from app.config.database import get_db, engine, Base
from app.config.settings import settings
from typing import Dict, Any, List, Optional
import traceback

router = APIRouter()

# Estado global de migraciones
migration_status = {
    "running": False,
    "last_run": None,
    "last_result": None,
    "logs": []
}

def log_migration(message: str):
    """Agrega un mensaje al log de migraciones"""
    print(f"[MIGRATION] {message}")
    migration_status["logs"].append(message)
    if len(migration_status["logs"]) > 100:
        migration_status["logs"] = migration_status["logs"][-100:]

def check_table_exists(table_name: str) -> bool:
    """Verifica si una tabla existe en la base de datos"""
    inspector = inspect(engine)
    return inspector.has_table(table_name)

def check_column_exists(table_name: str, column_name: str) -> bool:
    """Verifica si una columna existe en una tabla"""
    inspector = inspect(engine)
    if not inspector.has_table(table_name):
        return False
    columns = [c["name"] for c in inspector.get_columns(table_name)]
    return column_name in columns

def run_pdm_migrations(db: Session) -> List[str]:
    """Ejecuta migraciones relacionadas con PDM"""
    results = []
    
    try:
        # 1. Verificar y crear tabla pdm_actividades si no existe
        if not check_table_exists("pdm_actividades"):
            log_migration("Creando tabla pdm_actividades...")
            db.execute(text("""
                CREATE TABLE pdm_actividades (
                    id SERIAL PRIMARY KEY,
                    entity_id INTEGER NOT NULL,
                    producto TEXT NOT NULL,
                    indicador TEXT,
                    linea_base TEXT,
                    meta_cuatrienio TEXT,
                    tipo_indicador TEXT,
                    responsable TEXT,
                    corresponsables TEXT,
                    observaciones TEXT,
                    componente TEXT,
                    proceso TEXT,
                    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (entity_id) REFERENCES entities(id) ON DELETE CASCADE
                )
            """))
            db.commit()
            results.append("✓ Tabla pdm_actividades creada")
        else:
            results.append("✓ Tabla pdm_actividades ya existe")
        
        # 2. Agregar columnas de programación por año si no existen
        year_columns = [
            ("anio_1_meta", "TEXT"),
            ("anio_1_valor", "TEXT"),
            ("anio_2_meta", "TEXT"),
            ("anio_2_valor", "TEXT"),
            ("anio_3_meta", "TEXT"),
            ("anio_3_valor", "TEXT"),
            ("anio_4_meta", "TEXT"),
            ("anio_4_valor", "TEXT"),
        ]
        
        for col_name, col_type in year_columns:
            if not check_column_exists("pdm_actividades", col_name):
                log_migration(f"Agregando columna {col_name}...")
                db.execute(text(f"ALTER TABLE pdm_actividades ADD COLUMN {col_name} {col_type}"))
                db.commit()
                results.append(f"✓ Columna {col_name} agregada")
        
        # 3. Verificar y crear tabla actividades_evidencias si no existe
        if not check_table_exists("actividades_evidencias"):
            log_migration("Creando tabla actividades_evidencias...")
            db.execute(text("""
                CREATE TABLE actividades_evidencias (
                    id SERIAL PRIMARY KEY,
                    actividad_id INTEGER NOT NULL,
                    entity_id INTEGER NOT NULL,
                    nombre_archivo TEXT NOT NULL,
                    ruta_archivo TEXT NOT NULL,
                    tipo_archivo TEXT,
                    tamano_bytes INTEGER,
                    descripcion TEXT,
                    subido_por INTEGER,
                    fecha_subida TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (actividad_id) REFERENCES pdm_actividades(id) ON DELETE CASCADE,
                    FOREIGN KEY (entity_id) REFERENCES entities(id) ON DELETE CASCADE,
                    FOREIGN KEY (subido_por) REFERENCES users(id) ON DELETE SET NULL
                )
            """))
            db.commit()
            results.append("✓ Tabla actividades_evidencias creada")
        else:
            results.append("✓ Tabla actividades_evidencias ya existe")
        
        # 4. Agregar índices para mejorar performance
        try:
            db.execute(text("CREATE INDEX IF NOT EXISTS idx_pdm_actividades_entity ON pdm_actividades(entity_id)"))
            db.execute(text("CREATE INDEX IF NOT EXISTS idx_pdm_actividades_responsable ON pdm_actividades(responsable)"))
            db.execute(text("CREATE INDEX IF NOT EXISTS idx_pdm_actividades_entity_codigo ON pdm_actividades(entity_id, codigo_indicador_producto)"))
            db.execute(text("CREATE INDEX IF NOT EXISTS idx_evidencias_actividad ON actividades_evidencias(actividad_id)"))
            db.commit()
            results.append("✓ Índices creados/verificados")
        except Exception as e:
            results.append(f"⚠ Índices: {str(e)}")
        
    except Exception as e:
        error_msg = f"❌ Error en migraciones PDM: {str(e)}"
        log_migration(error_msg)
        results.append(error_msg)
        db.rollback()
    
    return results

def run_planes_migrations(db: Session) -> List[str]:
    """Ejecuta migraciones relacionadas con Planes Institucionales"""
    results = []
    
    try:
        # Verificar que la tabla planes_institucionales existe
        if check_table_exists("planes_institucionales"):
            results.append("✓ Tabla planes_institucionales existe")
            
            # Agregar columna entity_id si no existe
            if not check_column_exists("planes_institucionales", "entity_id"):
                log_migration("Agregando entity_id a planes_institucionales...")
                db.execute(text("""
                    ALTER TABLE planes_institucionales 
                    ADD COLUMN entity_id INTEGER REFERENCES entities(id) ON DELETE CASCADE
                """))
                db.commit()
                results.append("✓ Columna entity_id agregada a planes_institucionales")
        
        # Verificar tabla componentes_proceso
        if check_table_exists("componentes_proceso"):
            results.append("✓ Tabla componentes_proceso existe")
        
        # Verificar tabla actividades
        if check_table_exists("actividades"):
            results.append("✓ Tabla actividades existe")
            
            # Verificar columna responsable existe
            if check_column_exists("actividades", "responsable"):
                results.append("✓ Columna responsable existe en actividades")
            else:
                log_migration("Agregando columna responsable a actividades...")
                db.execute(text("ALTER TABLE actividades ADD COLUMN responsable TEXT"))
                db.commit()
                results.append("✓ Columna responsable agregada")
        
        # Verificar tabla actividades_ejecucion
        if check_table_exists("actividades_ejecucion"):
            results.append("✓ Tabla actividades_ejecucion existe")
            
    except Exception as e:
        error_msg = f"❌ Error en migraciones Planes: {str(e)}"
        log_migration(error_msg)
        results.append(error_msg)
        db.rollback()
    
    return results

def run_secretarias_migrations(db: Session) -> List[str]:
    """Ejecuta migraciones relacionadas con Secretarías"""
    results = []
    
    try:
        # Verificar y crear tabla secretarias si no existe
        if not check_table_exists("secretarias"):
            log_migration("Creando tabla secretarias...")
            db.execute(text("""
                CREATE TABLE secretarias (
                    id SERIAL PRIMARY KEY,
                    entity_id INTEGER NOT NULL,
                    nombre TEXT NOT NULL,
                    descripcion TEXT,
                    activo BOOLEAN DEFAULT TRUE,
                    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (entity_id) REFERENCES entities(id) ON DELETE CASCADE
                )
            """))
            db.commit()
            results.append("✓ Tabla secretarias creada")
            
            # Crear índice
            db.execute(text("CREATE INDEX IF NOT EXISTS idx_secretarias_entity ON secretarias(entity_id)"))
            db.commit()
            results.append("✓ Índice de secretarias creado")
        else:
            results.append("✓ Tabla secretarias ya existe")
            
    except Exception as e:
        error_msg = f"❌ Error en migraciones Secretarías: {str(e)}"
        log_migration(error_msg)
        results.append(error_msg)
        db.rollback()
    
    return results

def run_alerts_migrations(db: Session) -> List[str]:
    """Ejecuta migraciones relacionadas con Alertas"""
    results = []
    
    try:
        # Verificar tabla alerts
        if check_table_exists("alerts"):
            results.append("✓ Tabla alerts existe")
            
            # Verificar columnas necesarias
            required_columns = ["tipo", "titulo", "mensaje", "leido", "user_id", "entity_id"]
            missing = [col for col in required_columns if not check_column_exists("alerts", col)]
            
            if not missing:
                results.append("✓ Todas las columnas de alerts están presentes")
            else:
                results.append(f"⚠ Columnas faltantes en alerts: {', '.join(missing)}")
        else:
            results.append("⚠ Tabla alerts no existe (se creará con Base.metadata.create_all)")
            
    except Exception as e:
        error_msg = f"❌ Error en migraciones Alerts: {str(e)}"
        log_migration(error_msg)
        results.append(error_msg)
    
    return results

@router.post("/migrations/run")
async def run_migrations(
    db: Session = Depends(get_db),
    x_migration_key: Optional[str] = Header(None)
):
    """
    Ejecuta todas las migraciones pendientes en la base de datos.
    Requiere clave secreta en header X-Migration-Key.
    
    Uso con curl:
    ```bash
    curl -X POST https://tu-dominio.com/api/migrations/run \
      -H "X-Migration-Key: tu-clave-secreta-2024"
    ```
    """
    # Verificar clave de migración
    if not x_migration_key or x_migration_key != settings.migration_secret_key:
        raise HTTPException(
            status_code=403, 
            detail="Clave de migración inválida. Usa el header X-Migration-Key con la clave correcta."
        )
    
    if migration_status["running"]:
        return {
            "status": "already_running",
            "message": "Ya hay una migración en ejecución",
            "last_run": migration_status["last_run"]
        }
    
    migration_status["running"] = True
    migration_status["logs"] = []
    all_results = []
    
    try:
        log_migration("=== Iniciando migraciones ===")
        
        # 1. Crear todas las tablas base
        log_migration("Creando tablas base con SQLAlchemy...")
        Base.metadata.create_all(bind=engine)
        all_results.append("✓ Tablas base creadas/verificadas")
        
        # 2. Migraciones PDM
        log_migration("Ejecutando migraciones PDM...")
        pdm_results = run_pdm_migrations(db)
        all_results.extend(pdm_results)
        
        # 3. Migraciones Planes
        log_migration("Ejecutando migraciones Planes...")
        planes_results = run_planes_migrations(db)
        all_results.extend(planes_results)
        
        # 4. Migraciones Secretarías
        log_migration("Ejecutando migraciones Secretarías...")
        secretarias_results = run_secretarias_migrations(db)
        all_results.extend(secretarias_results)
        
        # 5. Migraciones Alertas
        log_migration("Ejecutando migraciones Alertas...")
        alerts_results = run_alerts_migrations(db)
        all_results.extend(alerts_results)
        
        log_migration("=== Migraciones completadas ===")
        
        from datetime import datetime
        migration_status["last_run"] = datetime.now().isoformat()
        migration_status["last_result"] = "success"
        
        return {
            "status": "success",
            "message": "Migraciones ejecutadas exitosamente",
            "results": all_results,
            "logs": migration_status["logs"]
        }
        
    except Exception as e:
        error_msg = f"Error ejecutando migraciones: {str(e)}"
        log_migration(f"❌ {error_msg}")
        log_migration(traceback.format_exc())
        
        from datetime import datetime
        migration_status["last_run"] = datetime.now().isoformat()
        migration_status["last_result"] = "error"
        
        return {
            "status": "error",
            "message": error_msg,
            "results": all_results,
            "logs": migration_status["logs"],
            "traceback": traceback.format_exc()
        }
    
    finally:
        migration_status["running"] = False

@router.get("/migrations/status")
async def get_migration_status(db: Session = Depends(get_db)):
    """
    Obtiene el estado actual de las tablas y migraciones.
    No requiere autenticación para facilitar debugging.
    
    Uso con curl:
    ```bash
    curl https://tu-dominio.com/api/migrations/status
    ```
    """
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        # Verificar tablas críticas
        critical_tables = {
            "users": check_table_exists("users"),
            "entities": check_table_exists("entities"),
            "planes_institucionales": check_table_exists("planes_institucionales"),
            "componentes_proceso": check_table_exists("componentes_proceso"),
            "actividades": check_table_exists("actividades"),
            "pdm_actividades": check_table_exists("pdm_actividades"),
            "actividades_evidencias": check_table_exists("actividades_evidencias"),
            "secretarias": check_table_exists("secretarias"),
            "alerts": check_table_exists("alerts"),
        }
        
        # Contar registros en tablas principales
        counts = {}
        for table in ["users", "entities", "pdm_actividades", "planes_institucionales", "secretarias"]:
            if check_table_exists(table):
                try:
                    result = db.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    counts[table] = result.scalar()
                except Exception as e:
                    counts[table] = f"Error: {str(e)}"
        
        # Verificar conexión a la base de datos
        db.execute(text("SELECT 1"))
        
        return {
            "status": "ok",
            "database_connected": True,
            "total_tables": len(tables),
            "all_tables": tables,
            "critical_tables": critical_tables,
            "record_counts": counts,
            "migration_history": {
                "running": migration_status["running"],
                "last_run": migration_status["last_run"],
                "last_result": migration_status["last_result"],
                "recent_logs": migration_status["logs"][-10:] if migration_status["logs"] else []
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "database_connected": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }
