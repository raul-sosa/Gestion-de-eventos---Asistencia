-- ============================================
-- Script SQL para crear todas las tablas en Supabase
-- ============================================
-- Ejecutar este script en Supabase SQL Editor

-- Tabla de usuarios
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT,
    password TEXT NOT NULL,
    full_name TEXT,
    role TEXT NOT NULL CHECK(role IN ('admin', 'encargado', 'estudiante')),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Tabla de eventos
CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY,
    nombre TEXT NOT NULL,
    descripcion TEXT,
    fecha_hora_inicio TIMESTAMP NOT NULL,
    fecha_hora_fin TIMESTAMP,
    ubicacion TEXT,
    capacidad_maxima INTEGER,
    estado TEXT NOT NULL CHECK(estado IN ('activo', 'finalizado', 'cancelado')) DEFAULT 'activo',
    organizador_id TEXT NOT NULL,
    imagen_url TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    FOREIGN KEY (organizador_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Tabla de estudiantes
CREATE TABLE IF NOT EXISTS students (
    id TEXT PRIMARY KEY,
    matricula TEXT UNIQUE NOT NULL,
    nombre TEXT NOT NULL,
    carrera TEXT,
    semestre INTEGER,
    email TEXT
);

-- Tabla de pre-registros
CREATE TABLE IF NOT EXISTS pre_registros (
    id TEXT PRIMARY KEY,
    id_evento TEXT NOT NULL,
    id_estudiante TEXT NOT NULL,
    matricula TEXT NOT NULL,
    fecha_registro TIMESTAMP NOT NULL DEFAULT NOW(),
    FOREIGN KEY (id_evento) REFERENCES events(id) ON DELETE CASCADE,
    UNIQUE(id_evento, matricula)
);

-- Tabla de asistencias
CREATE TABLE IF NOT EXISTS attendances (
    id TEXT PRIMARY KEY,
    id_credencial TEXT NOT NULL,
    id_evento TEXT NOT NULL,
    hora_registro TIMESTAMP NOT NULL DEFAULT NOW(),
    validado BOOLEAN NOT NULL DEFAULT FALSE,
    FOREIGN KEY (id_evento) REFERENCES events(id) ON DELETE CASCADE,
    UNIQUE(id_credencial, id_evento)
);

-- Índices para mejorar rendimiento
CREATE INDEX IF NOT EXISTS idx_events_estado ON events(estado);
CREATE INDEX IF NOT EXISTS idx_events_organizador ON events(organizador_id);
CREATE INDEX IF NOT EXISTS idx_events_fecha ON events(fecha_hora_inicio);
CREATE INDEX IF NOT EXISTS idx_attendances_evento ON attendances(id_evento);
CREATE INDEX IF NOT EXISTS idx_attendances_validado ON attendances(validado);
CREATE INDEX IF NOT EXISTS idx_attendances_credencial ON attendances(id_credencial);
CREATE INDEX IF NOT EXISTS idx_pre_registros_evento ON pre_registros(id_evento);
CREATE INDEX IF NOT EXISTS idx_pre_registros_matricula ON pre_registros(matricula);
CREATE INDEX IF NOT EXISTS idx_students_matricula ON students(matricula);

-- Verificar que las tablas se crearon correctamente
SELECT 
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count
FROM information_schema.tables t
WHERE table_schema = 'public' 
AND table_name IN ('users', 'events', 'students', 'pre_registros', 'attendances')
ORDER BY table_name;
