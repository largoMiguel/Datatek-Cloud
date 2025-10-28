#!/usr/bin/env python
"""Script de prueba para crear planes de ejemplo y verificar filtrado por entidad"""
import sys
from datetime import date, timedelta
from app.config.database import engine, get_db
from app.models.plan import PlanInstitucional, Meta, EstadoPlan, EstadoMeta
from sqlalchemy.orm import Session

def crear_plan_ejemplo(db: Session, entity_id: int, nombre_entidad: str):
    """Crea un plan de ejemplo para una entidad específica"""
    anio_actual = date.today().year
    
    plan = PlanInstitucional(
        nombre=f"Plan de Desarrollo {nombre_entidad} {anio_actual}",
        descripcion=f"Plan institucional de ejemplo para {nombre_entidad}",
        anio=anio_actual,
        fecha_inicio=date.today(),
        fecha_fin=date.today() + timedelta(days=365),
        estado=EstadoPlan.ACTIVO,
        entity_id=entity_id
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    
    print(f"✅ Plan creado: ID {plan.id} - '{plan.nombre}' para entity_id={entity_id}")
    
    # Crear una meta de ejemplo
    meta = Meta(
        plan_id=plan.id,
        nombre="Meta de ejemplo",
        descripcion="Meta de prueba para verificar el sistema",
        indicador="Porcentaje de cumplimiento",
        meta_numerica=100,
        avance_actual=0,
        fecha_inicio=date.today(),
        fecha_fin=date.today() + timedelta(days=180),
        responsable="Secretaría de Planeación",
        estado=EstadoMeta.NO_INICIADA,
        resultado=""
    )
    db.add(meta)
    db.commit()
    print(f"   ↳ Meta creada: ID {meta.id} - '{meta.nombre}'")
    
    return plan

def listar_planes_por_entidad(db: Session):
    """Lista todos los planes agrupados por entidad"""
    from sqlalchemy import text
    
    result = db.execute(text("""
        SELECT p.id, p.nombre, p.anio, p.entity_id, e.name as entidad_nombre
        FROM planes_institucionales p
        JOIN entities e ON p.entity_id = e.id
        ORDER BY p.entity_id, p.id
    """))
    
    print("\n=== PLANES POR ENTIDAD ===")
    current_entity = None
    for row in result:
        if current_entity != row[3]:
            current_entity = row[3]
            print(f"\n📁 ENTIDAD: {row[4]} (ID: {row[3]})")
        print(f"   • Plan ID {row[0]}: '{row[1]}' - Año {row[2]}")

def main():
    db = next(get_db())
    
    try:
        from sqlalchemy import text
        
        # Obtener entidades disponibles
        result = db.execute(text("SELECT id, name, slug FROM entities WHERE is_active = TRUE ORDER BY id"))
        entidades = list(result)
        
        if not entidades:
            print("❌ No hay entidades activas en la base de datos")
            return
        
        print("=== ENTIDADES DISPONIBLES ===")
        for e in entidades:
            print(f"{e[0]}. {e[1]} ({e[2]})")
        
        # Preguntar si crear planes de ejemplo
        print("\n¿Deseas crear planes de ejemplo para todas las entidades? (s/n): ", end='')
        respuesta = input().strip().lower()
        
        if respuesta == 's':
            for entity_id, nombre, slug in entidades:
                crear_plan_ejemplo(db, entity_id, nombre)
            
            print("\n✅ Planes de ejemplo creados exitosamente")
            listar_planes_por_entidad(db)
        else:
            print("\nListando planes existentes...")
            listar_planes_por_entidad(db)
            
            # Verificar si hay planes
            count = db.execute(text("SELECT COUNT(*) FROM planes_institucionales")).scalar()
            if count == 0:
                print("\n⚠️  No hay planes en la base de datos")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
