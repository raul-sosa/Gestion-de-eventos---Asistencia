-- ============================================
-- Script de migración: imagen_path → imagen_url
-- ============================================
-- Ejecutar SOLO si ya tienes una base de datos con la columna imagen_path
-- Para bases de datos nuevas, este script NO es necesario

-- Para PostgreSQL (Supabase)
ALTER TABLE events RENAME COLUMN imagen_path TO imagen_url;

-- Para SQLite (desarrollo local)
-- SQLite no soporta RENAME COLUMN directamente en versiones antiguas
-- Si usas SQLite < 3.25.0, necesitas recrear la tabla:
/*
BEGIN TRANSACTION;

CREATE TABLE events_new (
    id TEXT PRIMARY KEY,
    nombre TEXT NOT NULL,
    descripcion TEXT,
    fecha_hora_inicio TEXT NOT NULL,
    fecha_hora_fin TEXT,
    ubicacion TEXT,
    capacidad_maxima INTEGER,
    estado TEXT NOT NULL CHECK(estado IN ('activo', 'finalizado', 'cancelado')) DEFAULT 'activo',
    organizador_id TEXT NOT NULL,
    imagen_url TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (organizador_id) REFERENCES users(id)
);

INSERT INTO events_new SELECT 
    id, nombre, descripcion, fecha_hora_inicio, fecha_hora_fin,
    ubicacion, capacidad_maxima, estado, organizador_id,
    imagen_path, created_at, updated_at
FROM events;

DROP TABLE events;
ALTER TABLE events_new RENAME TO events;

COMMIT;
*/

-- Verificar que la migración fue exitosa
SELECT id, nombre, imagen_url FROM events LIMIT 5;
