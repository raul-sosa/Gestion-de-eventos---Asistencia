-- ============================================
-- Script SQL para crear usuarios por defecto en Supabase
-- ============================================
-- Ejecutar este script en Supabase SQL Editor después de crear las tablas
-- Los hashes bcrypt fueron generados con factor de costo 12

-- Eliminar usuarios existentes si ya existen (opcional)
DELETE FROM users WHERE username IN ('admin', 'encargado', 'estudiante');

-- Insertar usuario Admin
-- Username: admin, Password: admin123
INSERT INTO users (id, username, email, password, full_name, role, created_at)
VALUES (
    'admin-default-uuid-0001',
    'admin',
    'admin@eventos.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqVr/qvziu',
    'Administrador',
    'admin',
    NOW()
);

-- Insertar usuario Encargado
-- Username: encargado, Password: encargado123
INSERT INTO users (id, username, email, password, full_name, role, created_at)
VALUES (
    'encargado-default-uuid-0002',
    'encargado',
    'encargado@eventos.com',
    '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn6dNNqO5B3KO/LeISocLm7pjUS6',
    'Encargado de Asistencia',
    'encargado',
    NOW()
);

-- Insertar usuario Estudiante
-- Username: estudiante, Password: estudiante123
INSERT INTO users (id, username, email, password, full_name, role, created_at)
VALUES (
    'estudiante-default-uuid-0003',
    'estudiante',
    'estudiante@eventos.com',
    '$2b$12$wuyfLWmBZDzDd.WTOi0lxOReWGBfcXPWkO.U.ldbCH9ksfHdKRoXK',
    'Estudiante Prueba',
    'estudiante',
    NOW()
);

-- Verificar que los usuarios se crearon correctamente
SELECT id, username, email, full_name, role, created_at 
FROM users 
WHERE username IN ('admin', 'encargado', 'estudiante');

-- ============================================
-- NOTA: Si necesitas regenerar los hashes bcrypt con Python:
-- ============================================
-- import bcrypt
-- password = "admin123"
-- hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12))
-- print(hashed.decode('utf-8'))
