from app.config.database import Base, engine
from app.models.pdm import PdmMetaAssignment, PdmAvance

def main():
    # Crear solo las tablas PDM si no existen
    Base.metadata.create_all(bind=engine, tables=[
        PdmMetaAssignment.__table__,
        PdmAvance.__table__,
    ])
    print("Tablas PDM creadas o ya existentes.")

if __name__ == "__main__":
    main()
