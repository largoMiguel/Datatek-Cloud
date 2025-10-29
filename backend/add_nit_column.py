from sqlalchemy import create_engine, text
from app.config.settings import settings

def main():
    engine = create_engine(settings.database_url)
    with engine.connect() as conn:
        try:
            # Agregar columna NIT
            conn.execute(text("ALTER TABLE entities ADD COLUMN IF NOT EXISTS nit VARCHAR(50)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_entities_nit ON entities(nit)"))
            conn.commit()
            print("✓ Columna 'nit' agregada exitosamente a la tabla entities")
        except Exception as e:
            print(f"⚠️  Error: {e}")

if __name__ == "__main__":
    main()
