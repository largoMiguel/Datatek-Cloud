"""
Wrapper para ejecutar la migración local de campos en pdm_actividades.

Uso:
	cd backend
	python add_anio_meta_valor_to_pdm_actividades.py
"""
from scripts.migrate_pdm_actividades_fields import apply_migration

if __name__ == "__main__":
	apply_migration()
