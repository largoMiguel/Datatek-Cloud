#!/usr/bin/env python
"""Script para verificar datos en la base de datos"""
from app.config.database import engine
from sqlalchemy import text

conn = engine.connect()

# Entidades
result_entities = conn.execute(text('SELECT id, name, slug FROM entities ORDER BY id'))
print('\n=== ENTIDADES EN LA BD ===')
entities = list(result_entities)
for e in entities:
    print(f'ID: {e[0]}, Nombre: {e[1]}, Slug: {e[2]}')

# Usuarios
result_users = conn.execute(text('SELECT id, username, role, entity_id FROM users ORDER BY id'))
print('\n=== USUARIOS EN LA BD ===')
for u in result_users:
    print(f'ID: {u[0]}, Username: {u[1]}, Role: {u[2]}, Entity ID: {u[3]}')

# Planes
result_planes = conn.execute(text('SELECT id, nombre, anio, entity_id FROM planes_institucionales ORDER BY id'))
print('\n=== PLANES EN LA BD ===')
planes = list(result_planes)
if not planes:
    print('(No hay planes)')
else:
    for p in planes:
        print(f'ID: {p[0]}, Nombre: {p[1]}, Año: {p[2]}, Entity ID: {p[3]}')

conn.close()
