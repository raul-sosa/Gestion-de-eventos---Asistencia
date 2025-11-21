"""
Base de datos compartida para todos los microservicios
Usa SQLite con estructura SQL estándar
"""
import sqlite3
import json
import os
from datetime import datetime
from typing import Optional, List, Dict, Any

DB_PATH = os.path.join(os.path.dirname(__file__), "asistencias.db")

def get_connection():
    """Obtiene una conexión a la base de datos"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Para acceder a columnas por nombre
    return conn

def init_database():
    """Inicializa la base de datos con todas las tablas"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Tabla de usuarios
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            email TEXT,
            password TEXT NOT NULL,
            full_name TEXT,
            role TEXT NOT NULL CHECK(role IN ('admin', 'encargado', 'estudiante')),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabla de eventos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id TEXT PRIMARY KEY,
            nombre TEXT NOT NULL,
            descripcion TEXT,
            fecha_hora_inicio TEXT NOT NULL,
            fecha_hora_fin TEXT,
            ubicacion TEXT,
            capacidad_maxima INTEGER,
            estado TEXT NOT NULL CHECK(estado IN ('activo', 'finalizado', 'cancelado')) DEFAULT 'activo',
            organizador_id TEXT NOT NULL,
            imagen_path TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (organizador_id) REFERENCES users(id)
        )
    ''')
    
    # Tabla de estudiantes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id TEXT PRIMARY KEY,
            matricula TEXT UNIQUE NOT NULL,
            nombre TEXT NOT NULL,
            carrera TEXT,
            semestre INTEGER,
            email TEXT
        )
    ''')
    
    # Tabla de pre-registros
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pre_registros (
            id TEXT PRIMARY KEY,
            id_evento TEXT NOT NULL,
            id_estudiante TEXT NOT NULL,
            matricula TEXT NOT NULL,
            fecha_registro TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (id_evento) REFERENCES events(id) ON DELETE CASCADE,
            UNIQUE(id_evento, matricula)
        )
    ''')
    
    # Tabla de asistencias
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendances (
            id TEXT PRIMARY KEY,
            id_credencial TEXT NOT NULL,
            id_evento TEXT NOT NULL,
            hora_registro TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            validado INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (id_evento) REFERENCES events(id) ON DELETE CASCADE,
            UNIQUE(id_credencial, id_evento)
        )
    ''')
    
    # Índices para mejorar rendimiento
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_estado ON events(estado)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_organizador ON events(organizador_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_attendances_evento ON attendances(id_evento)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_attendances_validado ON attendances(validado)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_pre_registros_evento ON pre_registros(id_evento)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_students_matricula ON students(matricula)')
    
    conn.commit()
    conn.close()
    print(f"✓ Base de datos inicializada en: {DB_PATH}")

def migrate_from_json():
    """Migra datos existentes de JSON a SQL"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Migrar usuarios
    users_json_path = os.path.join(os.path.dirname(__file__), "users-service", "users_db.json")
    if os.path.exists(users_json_path):
        with open(users_json_path, 'r', encoding='utf-8') as f:
            users_data = json.load(f)
            for user in users_data.get("users", []):
                try:
                    cursor.execute('''
                        INSERT OR IGNORE INTO users (id, username, password, role, created_at)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (user['id'], user['username'], user['password'], user['role'], user['created_at']))
                except Exception as e:
                    print(f"Error migrando usuario {user.get('username')}: {e}")
        print(f"✓ Usuarios migrados: {cursor.rowcount}")
    
    # Migrar eventos, asistencias, pre-registros y estudiantes
    events_json_path = os.path.join(os.path.dirname(__file__), "events-service", "events_db.json")
    if os.path.exists(events_json_path):
        with open(events_json_path, 'r', encoding='utf-8') as f:
            events_data = json.load(f)
            
            # Migrar eventos
            for event in events_data.get("events", []):
                try:
                    cursor.execute('''
                        INSERT OR IGNORE INTO events 
                        (id, nombre, descripcion, fecha_hora_inicio, fecha_hora_fin, ubicacion, 
                         capacidad_maxima, estado, organizador_id, imagen_path, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        event['id'], event['nombre'], event.get('descripcion'),
                        event['fecha_hora_inicio'], event.get('fecha_hora_fin'),
                        event.get('ubicacion'), event.get('capacidad_maxima'),
                        event['estado'], event['organizador_id'],
                        event.get('imagen_url'),  # Renombrar de imagen_url a imagen_path
                        event['created_at'], event['updated_at']
                    ))
                except Exception as e:
                    print(f"Error migrando evento {event.get('nombre')}: {e}")
            print(f"✓ Eventos migrados")
            
            # Migrar asistencias
            for att in events_data.get("attendances", []):
                try:
                    cursor.execute('''
                        INSERT OR IGNORE INTO attendances 
                        (id, id_credencial, id_evento, hora_registro, validado)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        att['id'], att['id_credencial'], att['id_evento'],
                        att['hora_registro'], 1 if att['validado'] else 0
                    ))
                except Exception as e:
                    print(f"Error migrando asistencia: {e}")
            print(f"✓ Asistencias migradas")
            
            # Migrar pre-registros
            for pre_reg in events_data.get("pre_registros", []):
                try:
                    cursor.execute('''
                        INSERT OR IGNORE INTO pre_registros 
                        (id, id_evento, id_estudiante, matricula, fecha_registro)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        pre_reg['id'], pre_reg['id_evento'], pre_reg['id_estudiante'],
                        pre_reg.get('matricula', '00000'),  # Default si no existe
                        pre_reg['fecha_registro']
                    ))
                except Exception as e:
                    print(f"Error migrando pre-registro: {e}")
            print(f"✓ Pre-registros migrados")
            
            # Migrar estudiantes
            for student in events_data.get("students", []):
                try:
                    cursor.execute('''
                        INSERT OR IGNORE INTO students 
                        (id, matricula, nombre, carrera, semestre, email)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        student['id'], student['matricula'], student['nombre'],
                        student.get('carrera'), student.get('semestre'),
                        student.get('email')
                    ))
                except Exception as e:
                    print(f"Error migrando estudiante {student.get('matricula')}: {e}")
            print(f"✓ Estudiantes migrados")
    
    conn.commit()
    conn.close()
    print("✓ Migración completada")

def row_to_dict(row) -> Dict[str, Any]:
    """Convierte una fila de SQLite a diccionario"""
    if row is None:
        return None
    return dict(row)

def rows_to_list(rows) -> List[Dict[str, Any]]:
    """Convierte múltiples filas de SQLite a lista de diccionarios"""
    return [dict(row) for row in rows]

if __name__ == "__main__":
    print("Inicializando base de datos...")
    init_database()
    print("\nMigrando datos de JSON...")
    migrate_from_json()
    print("\n✓ Proceso completado")
