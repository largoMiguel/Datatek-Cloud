from sqlalchemy import create_engine, text
from app.config.settings import settings

def main():
    engine = create_engine(settings.database_url)
    with engine.connect() as conn:
        statements = [
            "ALTER TABLE entities ADD COLUMN IF NOT EXISTS enable_pqrs BOOLEAN NOT NULL DEFAULT TRUE",
            "ALTER TABLE entities ADD COLUMN IF NOT EXISTS enable_users_admin BOOLEAN NOT NULL DEFAULT TRUE",
            "ALTER TABLE entities ADD COLUMN IF NOT EXISTS enable_reports_pdf BOOLEAN NOT NULL DEFAULT TRUE",
            "ALTER TABLE entities ADD COLUMN IF NOT EXISTS enable_ai_reports BOOLEAN NOT NULL DEFAULT TRUE",
            "ALTER TABLE entities ADD COLUMN IF NOT EXISTS enable_planes_institucionales BOOLEAN NOT NULL DEFAULT TRUE"
        ]
        for sql in statements:
            try:
                conn.execute(text(sql))
                conn.commit()
                print(f"✓ {sql}")
            except Exception as e:
                print(f"⚠️  Error ejecutando: {sql} -> {e}")

if __name__ == "__main__":
    main()
