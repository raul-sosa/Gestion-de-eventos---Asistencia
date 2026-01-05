"""
Base de datos compartida para todos los microservicios
Usa SQLite con estructura SQL estándar o PostgreSQL según DATABASE_URL
"""
import logging
import sqlite3
import json
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
from contextlib import contextmanager
import time

DB_PATH = os.path.join(os.path.dirname(__file__), "asistencias.db")

# Cargar variables de entorno desde el archivo .env en la raíz del proyecto
load_dotenv(dotenv_path="../.env")

# Configurar logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Pool de conexiones PostgreSQL (se inicializa bajo demanda)
_pg_pool = None
_pool_lock = None

def _init_pg_pool():
    """Inicializa el pool de conexiones PostgreSQL."""
    global _pg_pool, _pool_lock
    if _pg_pool is not None:
        return
    
    import threading
    from psycopg_pool import ConnectionPool
    
    if _pool_lock is None:
        _pool_lock = threading.Lock()
    
    with _pool_lock:
        if _pg_pool is not None:
            return
        
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            return
        
        try:
            # Configurar SSL y timeouts en la URL si no están presentes
            if "sslmode=" not in db_url:
                db_url += "&sslmode=require" if "?" in db_url else "?sslmode=require"
            if "connect_timeout=" not in db_url:
                db_url += "&connect_timeout=10"
            
            # Forzar IPv4 para evitar problemas con IPv6 en Render
            if "hostaddr=" not in db_url:
                # Extraer el hostname y resolverlo a IPv4
                import re
                import socket
                # Extraer hostname: buscar entre @ y : (puerto)
                host_match = re.search(r'@([^:/?]+)', db_url)
                if host_match:
                    hostname = host_match.group(1)
                    try:
                        # Forzar resolución IPv4 solamente
                        ipv4_results = socket.getaddrinfo(hostname, None, socket.AF_INET, socket.SOCK_STREAM)
                        if ipv4_results:
                            ipv4_addr = ipv4_results[0][4][0]
                            db_url += f"&hostaddr={ipv4_addr}"
                            logger.info(f"Forzando IPv4: {hostname} -> {ipv4_addr}")
                    except Exception as e:
                        logger.warning(f"No se pudo resolver IPv4 para {hostname}: {e}")
            
            # Crear pool de conexiones con psycopg3
            _pg_pool = ConnectionPool(
                conninfo=db_url,
                min_size=1,
                max_size=10
            )
            logger.info("Pool de conexiones PostgreSQL inicializado correctamente")
        except Exception as e:
            logger.error(f"Error al inicializar pool PostgreSQL: {e}")
            _pg_pool = None

def _get_pg_connection():
    """Obtiene una conexión del pool PostgreSQL con reintentos."""
    import psycopg
    from psycopg.rows import dict_row
    
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        return None
    
    # Intentar usar pool si está disponible
    if _pg_pool is not None:
        try:
            conn = _pg_pool.getconn()
            if conn:
                return conn
        except Exception as e:
            logger.warning(f"Error obteniendo conexión del pool: {e}")
    
    # Fallback: conexión directa con reintentos
    max_retries = 3
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            # Asegurar SSL y timeout
            connection_params = db_url
            if "sslmode=" not in connection_params:
                connection_params += "&sslmode=require" if "?" in connection_params else "?sslmode=require"
            if "connect_timeout=" not in connection_params:
                connection_params += "&connect_timeout=10"
            
            # Forzar IPv4 para evitar problemas con IPv6 en Render
            if "hostaddr=" not in connection_params:
                import re
                import socket
                # Extraer hostname: buscar entre @ y : (puerto)
                host_match = re.search(r'@([^:/?]+)', connection_params)
                if host_match:
                    hostname = host_match.group(1)
                    try:
                        # Forzar resolución IPv4 solamente
                        ipv4_results = socket.getaddrinfo(hostname, None, socket.AF_INET, socket.SOCK_STREAM)
                        if ipv4_results:
                            ipv4_addr = ipv4_results[0][4][0]
                            connection_params += f"&hostaddr={ipv4_addr}"
                            logger.info(f"Forzando IPv4: {hostname} -> {ipv4_addr}")
                    except Exception as e:
                        logger.warning(f"No se pudo resolver IPv4 para {hostname}: {e}")
            
            # Intentar conexión con psycopg3
            conn = psycopg.connect(
                connection_params,
                row_factory=dict_row
            )
            logger.info(f"Conexión PostgreSQL establecida (intento {attempt + 1})")
            return conn
            
        except psycopg.OperationalError as e:
            error_msg = str(e).lower()
            
            # Si es timeout o problema de red, intentar puerto alternativo
            if "timeout" in error_msg or "could not connect" in error_msg:
                if ":5432" in db_url and attempt == 0:
                    logger.warning("Puerto 5432 falló, intentando puerto 6543 (connection pooler)...")
                    db_url = db_url.replace(":5432", ":6543")
                    continue
            
            if attempt < max_retries - 1:
                logger.warning(f"Intento {attempt + 1} falló: {e}. Reintentando en {retry_delay}s...")
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                logger.error(f"No se pudo conectar a PostgreSQL después de {max_retries} intentos: {e}")
                raise
        
        except Exception as e:
            logger.error(f"Error inesperado conectando a PostgreSQL: {e}")
            if attempt == max_retries - 1:
                raise
            time.sleep(retry_delay)
    
    return None

def get_connection():
    """Obtiene una conexión a la base de datos.
    Si DATABASE_URL apunta a PostgreSQL, usa psycopg2 con DictCursor y pool.
    En caso contrario, usa SQLite local.
    """
    db_url = os.getenv("DATABASE_URL")
    if db_url and db_url.startswith("postgres"):
        # Inicializar pool si es la primera vez
        if _pg_pool is None:
            _init_pg_pool()
        
        # Obtener conexión PostgreSQL
        conn = _get_pg_connection()
        if conn:
            return conn
        
        logger.warning("No se pudo obtener conexión PostgreSQL, usando SQLite como fallback")
    
    # Fallback a SQLite
    class SQLiteCompatCursor(sqlite3.Cursor):
        def execute(self, sql, parameters=None):
            if parameters is None:
                parameters = ()
            sql = sql.replace('%s', '?')
            return super().execute(sql, parameters)

        def executemany(self, sql, seq_of_parameters):
            sql = sql.replace('%s', '?')
            return super().executemany(sql, seq_of_parameters)

    class SQLiteCompatConnection(sqlite3.Connection):
        def cursor(self, factory=None):
            return super().cursor(factory or SQLiteCompatCursor)

    conn = sqlite3.connect(DB_PATH, factory=SQLiteCompatConnection)
    conn.row_factory = sqlite3.Row  # Para acceder a columnas por nombre
    logger.debug("Usando SQLite local")
    return conn

@contextmanager
def get_db_connection():
    """Context manager para manejar conexiones de forma segura."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Error en transacción de BD: {e}")
        raise
    finally:
        # Si es del pool, devolver al pool; si no, cerrar
        if _pg_pool is not None and os.getenv("DATABASE_URL", "").startswith("postgres"):
            try:
                _pg_pool.putconn(conn)
            except:
                conn.close()
        else:
            conn.close()

def init_database():
    """Inicializa la base de datos con todas las tablas"""
    logger.info("Inicializando base de datos...")
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
            imagen_url TEXT,
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
    logger.info(f"✓ Base de datos inicializada en: {DB_PATH}")

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
    """Convierte una fila de PostgreSQL a diccionario - psycopg3 compatible"""
    if row is None:
        return None
    # Con row_factory=dict_row, row ya es un dict
    if isinstance(row, dict):
        return row
    # Fallback para otros tipos
    if hasattr(row, '_asdict'):
        return row._asdict()
    elif hasattr(row, 'keys') and hasattr(row, 'values'):
        return dict(zip(row.keys(), row.values()))
    else:
        # Último recurso: intentar convertir directamente
        try:
            return dict(row)
        except (ValueError, TypeError):
            # Si falla, convertir a dict manualmente
            return {key: row[key] for key in row.keys()}

def rows_to_list(rows) -> List[Dict[str, Any]]:
    """Convierte múltiples filas de PostgreSQL a lista de diccionarios"""
    return [row_to_dict(row) for row in rows]

if __name__ == "__main__":
    print("Inicializando base de datos...")
    init_database()
    print("\nMigrando datos de JSON...")
    migrate_from_json()
    print("\n✓ Proceso completado")
