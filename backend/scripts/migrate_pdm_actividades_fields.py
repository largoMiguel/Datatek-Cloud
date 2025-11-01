"""
Migración local: agregar columnas anio, meta_ejecutar y valor_ejecutado a pdm_actividades

Uso:
    cd backend
    python -m scripts.migrate_pdm_actividades_fields

Lee la configuración de base de datos desde app.config.settings (DATABASE_URL)
Soporta PostgreSQL y SQLite.
"""
from sqlalchemy import text
from sqlalchemy import inspect as sa_inspect
from app.config.database import engine


def apply_migration():
    bind = engine
    inspector = sa_inspect(bind)

    if not inspector.has_table("pdm_actividades"):
        print("⚠️  La tabla 'pdm_actividades' no existe. Ejecuta migraciones base primero.")
        return

    dialect = bind.dialect.name
    is_postgres = dialect.startswith("postgres")

    # columnas existentes
    cols = {c["name"] for c in inspector.get_columns("pdm_actividades")}

    with bind.begin() as conn:
        # anio
        if "anio" not in cols:
            if is_postgres:
                conn.execute(text("ALTER TABLE pdm_actividades ADD COLUMN IF NOT EXISTS anio INTEGER"))
            else:
                conn.execute(text("ALTER TABLE pdm_actividades ADD COLUMN anio INTEGER"))
            print("🆕 Agregada columna 'anio' en pdm_actividades")
        else:
            print("ℹ️  Columna 'anio' ya existe en pdm_actividades")

        # meta_ejecutar
        if "meta_ejecutar" not in cols:
            if is_postgres:
                conn.execute(text("ALTER TABLE pdm_actividades ADD COLUMN IF NOT EXISTS meta_ejecutar FLOAT NOT NULL DEFAULT 0.0"))
            else:
                conn.execute(text("ALTER TABLE pdm_actividades ADD COLUMN meta_ejecutar REAL NOT NULL DEFAULT 0.0"))
            print("🆕 Agregada columna 'meta_ejecutar' en pdm_actividades")
        else:
            print("ℹ️  Columna 'meta_ejecutar' ya existe en pdm_actividades")

        # valor_ejecutado
        if "valor_ejecutado" not in cols:
            if is_postgres:
                conn.execute(text("ALTER TABLE pdm_actividades ADD COLUMN IF NOT EXISTS valor_ejecutado FLOAT NOT NULL DEFAULT 0.0"))
            else:
                conn.execute(text("ALTER TABLE pdm_actividades ADD COLUMN valor_ejecutado REAL NOT NULL DEFAULT 0.0"))
            print("🆕 Agregada columna 'valor_ejecutado' en pdm_actividades")
        else:
            print("ℹ️  Columna 'valor_ejecutado' ya existe en pdm_actividades")

    print("✅ Migración completada.")


if __name__ == "__main__":
    apply_migration()
