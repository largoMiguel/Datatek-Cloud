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
    """Ejecuta migraciones relacionadas con PDM alineadas al modelo actual."""
    results = []

    try:
        # 1) pdm_actividades
        if not check_table_exists("pdm_actividades"):
            log_migration("Creando tabla pdm_actividades (modelo actual)...")
            db.execute(text(
            # Verificar y agregar columnas necesarias de forma idempotente
            required_columns = {
                "tipo": "TEXT",
                "titulo": "TEXT",
                "mensaje": "TEXT",
                "leido": "BOOLEAN DEFAULT FALSE",
                "user_id": "INTEGER",
                "entity_id": "INTEGER",
            }

            missing_cols = []
            for col, col_type in required_columns.items():
                if not check_column_exists("alerts", col):
                    missing_cols.append(col)
                    log_migration(f"Agregando columna {col} a alerts...")
                    db.execute(text(f"ALTER TABLE alerts ADD COLUMN {col} {col_type}"))
                    # Añadir FK cuando aplique
                    if col == "user_id":
                        try:
                            db.execute(text("ALTER TABLE alerts ADD CONSTRAINT fk_alerts_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL"))
                        except Exception:
                            # Ignore FK creation failures (por ejemplo, si ya existe o faltan permisos)
                            pass
                    if col == "entity_id":
                        try:
                            db.execute(text("ALTER TABLE alerts ADD CONSTRAINT fk_alerts_entity FOREIGN KEY (entity_id) REFERENCES entities(id) ON DELETE CASCADE"))
                        except Exception:
                            pass
                    db.commit()
                    results.append(f"✓ Columna {col} agregada a alerts")

            if not missing_cols:
                results.append("✓ Todas las columnas de alerts están presentes")
                    fecha_inicio TIMESTAMP,
                    fecha_fin TIMESTAMP,
                    porcentaje_avance DOUBLE PRECISION DEFAULT 0 NOT NULL,
                    anio INTEGER,
                    meta_ejecutar DOUBLE PRECISION DEFAULT 0 NOT NULL,
                    valor_ejecutado DOUBLE PRECISION DEFAULT 0 NOT NULL,
                    estado TEXT DEFAULT 'pendiente' NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            ))
            db.commit()
            results.append("✓ Tabla pdm_actividades creada")
        else:
            results.append("✓ Tabla pdm_actividades ya existe")

            # Asegurar columnas clave según modelo
            required_cols = {
                "codigo_indicador_producto": "VARCHAR(128)",
                "nombre": "VARCHAR(512)",
                "descripcion": "VARCHAR(1024)",
                "responsable": "VARCHAR(256)",
                "fecha_inicio": "TIMESTAMP",
                "fecha_fin": "TIMESTAMP",
                "porcentaje_avance": "DOUBLE PRECISION DEFAULT 0",
                "anio": "INTEGER",
                "meta_ejecutar": "DOUBLE PRECISION DEFAULT 0",
                "valor_ejecutado": "DOUBLE PRECISION DEFAULT 0",
                "estado": "TEXT DEFAULT 'pendiente'",
                "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                "updated_at": "TIMESTAMP"
            }
            for col, tipo in required_cols.items():
                if not check_column_exists("pdm_actividades", col):
                    log_migration(f"Agregando columna {col} a pdm_actividades...")
                    db.execute(text(f"ALTER TABLE pdm_actividades ADD COLUMN {col} {tipo}"))
                    db.commit()
                    results.append(f"✓ Columna {col} agregada a pdm_actividades")

        # 2) Índices para pdm_actividades
        try:
            db.execute(text("CREATE INDEX IF NOT EXISTS idx_pdm_actividades_entity ON pdm_actividades(entity_id)"))
            db.execute(text("CREATE INDEX IF NOT EXISTS idx_pdm_actividades_codigo ON pdm_actividades(codigo_indicador_producto)"))
            db.execute(text("CREATE INDEX IF NOT EXISTS idx_pdm_actividades_entity_codigo ON pdm_actividades(entity_id, codigo_indicador_producto)"))
            db.commit()
            results.append("✓ Índices pdm_actividades verificados")
        except Exception as e:
            results.append(f"⚠ Índices pdm_actividades: {str(e)}")

        # 3) Evidencias de PDM: pdm_actividades_evidencias
        if not check_table_exists("pdm_actividades_evidencias"):
            log_migration("Creando tabla pdm_actividades_evidencias...")
            db.execute(text(
                """
                CREATE TABLE pdm_actividades_evidencias (
                    id SERIAL PRIMARY KEY,
                    actividad_id INTEGER NOT NULL REFERENCES pdm_actividades(id) ON DELETE CASCADE,
                    entity_id INTEGER NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
                    descripcion TEXT,
                    url VARCHAR(512),
                    nombre_imagen VARCHAR(256),
                    mime_type VARCHAR(64),
                    tamano INTEGER,
                    contenido BYTEA,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            ))
            db.commit()
            results.append("✓ Tabla pdm_actividades_evidencias creada")
        else:
            results.append("✓ Tabla pdm_actividades_evidencias ya existe")

        try:
            db.execute(text("CREATE INDEX IF NOT EXISTS idx_pdm_evidencias_actividad ON pdm_actividades_evidencias(actividad_id)"))
            db.commit()
            results.append("✓ Índices evidencias PDM verificados")
        except Exception as e:
            results.append(f"⚠ Índices evidencias PDM: {str(e)}")

    except Exception as e:
        error_msg = f"❌ Error en migraciones PDM: {str(e)}"
        log_migration(error_msg)
        results.append(error_msg)
        db.rollback()

    return results

def run_planes_migrations(db: Session) -> List[str]:
    """Ejecuta migraciones relacionadas con Planes Institucionales (idempotentes)."""
    results: List[str] = []

    try:
        # ===================== Planes =====================
        if check_table_exists("planes_institucionales"):
            results.append("✓ Tabla planes_institucionales existe")

            # Asegurar FK a entities
            if not check_column_exists("planes_institucionales", "entity_id"):
                log_migration("Agregando entity_id a planes_institucionales...")
                db.execute(text(
                    """
                    ALTER TABLE planes_institucionales 
                    ADD COLUMN entity_id INTEGER REFERENCES entities(id) ON DELETE CASCADE
                    """
                ))
                db.commit()
                results.append("✓ Columna entity_id agregada a planes_institucionales")

            # Columnas críticas (usamos tipos compatibles para evitar problemas con ENUMs existentes)
            columnas_requeridas = {
                "anio": "INTEGER",
                "nombre": "TEXT",
                "descripcion": "TEXT",
                "periodo_inicio": "DATE",
                "periodo_fin": "DATE",
                "estado": "TEXT",
                "porcentaje_avance": "NUMERIC(5,2) DEFAULT 0",
                "responsable_elaboracion": "TEXT",
                "responsable_aprobacion": "TEXT",
                "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                "updated_at": "TIMESTAMP",
                "created_by": "TEXT",
            }
            for col, tipo in columnas_requeridas.items():
                if not check_column_exists("planes_institucionales", col):
                    log_migration(f"Agregando columna {col} a planes_institucionales...")
                    db.execute(text(f"ALTER TABLE planes_institucionales ADD COLUMN {col} {tipo}"))
                    db.commit()
                    results.append(f"✓ Columna {col} agregada a planes_institucionales")

            # Índices
            try:
                db.execute(text("CREATE INDEX IF NOT EXISTS idx_planes_entity ON planes_institucionales(entity_id)"))
                db.execute(text("CREATE INDEX IF NOT EXISTS idx_planes_anio ON planes_institucionales(anio)"))
                db.execute(text("CREATE INDEX IF NOT EXISTS idx_planes_periodo_inicio ON planes_institucionales(periodo_inicio)"))
                db.execute(text("CREATE INDEX IF NOT EXISTS idx_planes_entity_anio ON planes_institucionales(entity_id, anio)"))
                db.commit()
                results.append("✓ Índices de planes verificados")
            except Exception as e:
                results.append(f"⚠ Índices de planes: {str(e)}")
        else:
            results.append("⚠ Tabla planes_institucionales no existe (se crea con Base.metadata.create_all)")

        # ===================== Componentes / Procesos =====================
        if check_table_exists("componentes_procesos"):
            results.append("✓ Tabla componentes_procesos existe")

            columnas_comp = {
                "nombre": "TEXT",
                "estado": "TEXT",
                "porcentaje_avance": "NUMERIC(5,2) DEFAULT 0",
                "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                "updated_at": "TIMESTAMP",
                "plan_id": "INTEGER REFERENCES planes_institucionales(id) ON DELETE CASCADE",
            }
            for col, tipo in columnas_comp.items():
                if not check_column_exists("componentes_procesos", col):
                    log_migration(f"Agregando columna {col} a componentes_procesos...")
                    db.execute(text(f"ALTER TABLE componentes_procesos ADD COLUMN {col} {tipo}"))
                    db.commit()
                    results.append(f"✓ Columna {col} agregada a componentes_procesos")

            # Índices
            try:
                db.execute(text("CREATE INDEX IF NOT EXISTS idx_componentes_plan ON componentes_procesos(plan_id)"))
                db.execute(text("CREATE INDEX IF NOT EXISTS idx_componentes_estado ON componentes_procesos(estado)"))
                db.commit()
                results.append("✓ Índices de componentes verificados")
            except Exception as e:
                results.append(f"⚠ Índices de componentes: {str(e)}")
        else:
            results.append("⚠ Tabla componentes_procesos no existe (se crea con Base.metadata.create_all)")

        # ===================== Actividades =====================
        if check_table_exists("actividades"):
            results.append("✓ Tabla actividades existe")

            columnas_act = {
                "objetivo_especifico": "TEXT",
                "fecha_inicio_prevista": "DATE",
                "fecha_fin_prevista": "DATE",
                "responsable": "TEXT",
                "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                "updated_at": "TIMESTAMP",
                "componente_id": "INTEGER REFERENCES componentes_procesos(id) ON DELETE CASCADE",
            }
            for col, tipo in columnas_act.items():
                if not check_column_exists("actividades", col):
                    log_migration(f"Agregando columna {col} a actividades...")
                    db.execute(text(f"ALTER TABLE actividades ADD COLUMN {col} {tipo}"))
                    db.commit()
                    results.append(f"✓ Columna {col} agregada a actividades")

            # Índices
            try:
                db.execute(text("CREATE INDEX IF NOT EXISTS idx_actividades_resp ON actividades(responsable)"))
                db.execute(text("CREATE INDEX IF NOT EXISTS idx_actividades_comp ON actividades(componente_id)"))
                db.execute(text("CREATE INDEX IF NOT EXISTS idx_actividades_inicio ON actividades(fecha_inicio_prevista)"))
                db.commit()
                results.append("✓ Índices de actividades verificados")
            except Exception as e:
                results.append(f"⚠ Índices de actividades: {str(e)}")
        else:
            results.append("⚠ Tabla actividades no existe (se crea con Base.metadata.create_all)")

        # ===================== Actividades de Ejecución =====================
        if check_table_exists("actividades_ejecucion"):
            results.append("✓ Tabla actividades_ejecucion existe")

            columnas_eje = {
                "fecha_registro": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                "descripcion": "TEXT",
                "evidencia_url": "VARCHAR(500)",
                "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                "updated_at": "TIMESTAMP",
                "actividad_id": "INTEGER REFERENCES actividades(id) ON DELETE CASCADE",
            }
            for col, tipo in columnas_eje.items():
                if not check_column_exists("actividades_ejecucion", col):
                    log_migration(f"Agregando columna {col} a actividades_ejecucion...")
                    db.execute(text(f"ALTER TABLE actividades_ejecucion ADD COLUMN {col} {tipo}"))
                    db.commit()
                    results.append(f"✓ Columna {col} agregada a actividades_ejecucion")

            # Índices
            try:
                db.execute(text("CREATE INDEX IF NOT EXISTS idx_ejecucion_actividad ON actividades_ejecucion(actividad_id)"))
                db.execute(text("CREATE INDEX IF NOT EXISTS idx_ejecucion_fecha ON actividades_ejecucion(fecha_registro)"))
                db.commit()
                results.append("✓ Índices de actividades_ejecucion verificados")
            except Exception as e:
                results.append(f"⚠ Índices de actividades_ejecucion: {str(e)}")
        else:
            results.append("⚠ Tabla actividades_ejecucion no existe (se crea con Base.metadata.create_all)")

        # ===================== Evidencias de Ejecución =====================
        if check_table_exists("actividades_evidencias"):
            results.append("✓ Tabla actividades_evidencias existe")

            columnas_evid = {
                "tipo": "TEXT",
                "contenido": "TEXT",
                "nombre_archivo": "VARCHAR(255)",
                "mime_type": "VARCHAR(100)",
                "orden": "INTEGER DEFAULT 0",
                "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                "actividad_ejecucion_id": "INTEGER REFERENCES actividades_ejecucion(id) ON DELETE CASCADE",
            }
            for col, tipo in columnas_evid.items():
                if not check_column_exists("actividades_evidencias", col):
                    log_migration(f"Agregando columna {col} a actividades_evidencias...")
                    db.execute(text(f"ALTER TABLE actividades_evidencias ADD COLUMN {col} {tipo}"))
                    db.commit()
                    results.append(f"✓ Columna {col} agregada a actividades_evidencias")

            # Índices
            try:
                db.execute(text("CREATE INDEX IF NOT EXISTS idx_evidencias_actividad_ejecucion ON actividades_evidencias(actividad_ejecucion_id)"))
                db.execute(text("CREATE INDEX IF NOT EXISTS idx_evidencias_tipo ON actividades_evidencias(tipo)"))
                db.commit()
                results.append("✓ Índices de actividades_evidencias verificados")
            except Exception as e:
                results.append(f"⚠ Índices de actividades_evidencias: {str(e)}")
        else:
            results.append("⚠ Tabla actividades_evidencias no existe (se crea con Base.metadata.create_all)")

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
            "componentes_procesos": check_table_exists("componentes_procesos"),
            "actividades": check_table_exists("actividades"),
            "actividades_ejecucion": check_table_exists("actividades_ejecucion"),
            "actividades_evidencias": check_table_exists("actividades_evidencias"),
            "pdm_actividades": check_table_exists("pdm_actividades"),
            "pdm_actividades_evidencias": check_table_exists("pdm_actividades_evidencias"),
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
