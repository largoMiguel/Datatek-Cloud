from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from app.config.settings import settings

COLUMNS = [
    ("enable_pqrs", "BOOLEAN NOT NULL DEFAULT 1"),
    ("enable_users_admin", "BOOLEAN NOT NULL DEFAULT 1"),
    ("enable_reports_pdf", "BOOLEAN NOT NULL DEFAULT 1"),
    ("enable_ai_reports", "BOOLEAN NOT NULL DEFAULT 1"),
    ("enable_planes_institucionales", "BOOLEAN NOT NULL DEFAULT 1"),
    ("enable_contratacion", "BOOLEAN NOT NULL DEFAULT 1"),
    ("enable_pdm", "BOOLEAN NOT NULL DEFAULT 1"),
]


def column_exists_sqlite(conn, table: str, column: str) -> bool:
    result = conn.execute(text(f"PRAGMA table_info('{table}')")).fetchall()
    existing = {row[1] for row in result}  # row[1] = name
    return column in existing


def ensure_columns(engine: Engine):
    with engine.connect() as conn:
        dialect = engine.dialect.name
        for col_name, col_def in COLUMNS:
            try:
                if dialect == 'sqlite':
                    if column_exists_sqlite(conn, 'entities', col_name):
                        print(f"✓ Column '{col_name}' ya existe (sqlite)")
                        continue
                    sql = f"ALTER TABLE entities ADD COLUMN {col_name} {col_def}"
                else:
                    # Postgres y otros soportan IF NOT EXISTS
                    sql = f"ALTER TABLE entities ADD COLUMN IF NOT EXISTS {col_name} {col_def.replace('1','TRUE').replace('0','FALSE')}"

                conn.execute(text(sql))
                conn.commit()
                print(f"✓ {sql}")
            except Exception as e:
                print(f"⚠️  Error ejecutando columna '{col_name}': {e}")


def main():
    engine = create_engine(settings.database_url)
    ensure_columns(engine)

if __name__ == "__main__":
    main()
