"""
Funciones helper para events-service usando SQL
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import get_connection, row_to_dict, rows_to_list
from datetime import datetime
import uuid

# ==================== HELPERS ====================

def convert_datetime_fields(event_dict):
    """Convierte campos datetime a string ISO para compatibilidad con Pydantic"""
    if event_dict:
        for field in ['fecha_hora_inicio', 'fecha_hora_fin', 'created_at', 'updated_at']:
            if field in event_dict and isinstance(event_dict[field], datetime):
                event_dict[field] = event_dict[field].isoformat()
    return event_dict

# ==================== EVENTOS ====================

def get_all_events(estado=None):
    conn = get_connection()
    cursor = conn.cursor()
    if estado:
        cursor.execute("SELECT * FROM events WHERE estado = %s ORDER BY created_at DESC", (estado,))
    else:
        cursor.execute("SELECT * FROM events ORDER BY created_at DESC")
    events = rows_to_list(cursor.fetchall())
    conn.close()
    # Convertir datetime a string en todos los eventos
    return [convert_datetime_fields(event) for event in events]

def get_event_by_id(event_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM events WHERE id = %s", (event_id,))
    event = cursor.fetchone()
    conn.close()
    event_dict = row_to_dict(event) if event else None
    return convert_datetime_fields(event_dict) if event_dict else None

def create_event_db(event_data, organizador_id):
    conn = get_connection()
    cursor = conn.cursor()
    event_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    cursor.execute('''
        INSERT INTO events (id, nombre, descripcion, fecha_hora_inicio, fecha_hora_fin, 
                           ubicacion, capacidad_maxima, estado, organizador_id, imagen_url, 
                           created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ''', (
        event_id, event_data.nombre, event_data.descripcion,
        event_data.fecha_hora_inicio, event_data.fecha_hora_fin,
        event_data.ubicacion, event_data.capacidad_maxima,
        'activo', organizador_id, event_data.imagen_url,
        now, now
    ))
    conn.commit()
    
    cursor.execute("SELECT * FROM events WHERE id = %s", (event_id,))
    new_event = row_to_dict(cursor.fetchone())
    conn.close()
    
    return convert_datetime_fields(new_event)

def update_event(event_id, event_data):
    conn = get_connection()
    cursor = conn.cursor()
    
    updates = []
    params = []
    
    if event_data.nombre is not None:
        updates.append("nombre = %s")
        params.append(event_data.nombre)
    if event_data.descripcion is not None:
        updates.append("descripcion = %s")
        params.append(event_data.descripcion)
    if event_data.fecha_hora_inicio is not None:
        updates.append("fecha_hora_inicio = %s")
        params.append(event_data.fecha_hora_inicio)
    if event_data.fecha_hora_fin is not None:
        updates.append("fecha_hora_fin = %s")
        params.append(event_data.fecha_hora_fin)
    if event_data.ubicacion is not None:
        updates.append("ubicacion = %s")
        params.append(event_data.ubicacion)
    if event_data.capacidad_maxima is not None:
        updates.append("capacidad_maxima = %s")
        params.append(event_data.capacidad_maxima)
    if event_data.estado is not None:
        updates.append("estado = %s")
        params.append(event_data.estado)
    if event_data.imagen_url is not None:
        updates.append("imagen_url = %s")
        params.append(event_data.imagen_url)
    
    updates.append("updated_at = %s")
    params.append(datetime.now().isoformat())
    params.append(event_id)
    
    query = f"UPDATE events SET {', '.join(updates)} WHERE id = %s"
    cursor.execute(query, params)
    conn.commit()
    
    cursor.execute("SELECT * FROM events WHERE id = %s", (event_id,))
    updated_event = row_to_dict(cursor.fetchone())
    conn.close()
    return convert_datetime_fields(updated_event)

def delete_event(event_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM events WHERE id = %s", (event_id,))
    conn.commit()
    conn.close()

# ==================== ASISTENCIAS ====================

def get_event_attendances(event_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM attendances WHERE id_evento = %s ORDER BY hora_registro DESC", (event_id,))
    attendances = rows_to_list(cursor.fetchall())
    
    if not attendances:
        conn.close()
        return []
    
    # Optimización: obtener todos los estudiantes en una sola query
    matriculas = [att['id_credencial'] for att in attendances]
    placeholders = ','.join(['%s'] * len(matriculas))
    cursor.execute(f"SELECT * FROM students WHERE matricula IN ({placeholders})", matriculas)
    students_rows = cursor.fetchall()
    
    # Crear diccionario de estudiantes por matrícula para búsqueda rápida
    students_dict = {row['matricula']: row_to_dict(row) for row in students_rows}
    
    # Enriquecer asistencias con información del estudiante
    for att in attendances:
        att['validado'] = bool(att['validado'])
        att['estudiante'] = students_dict.get(att['id_credencial'], None)
    
    conn.close()
    return attendances

def create_attendance(id_credencial, id_evento):
    conn = get_connection()
    cursor = conn.cursor()
    
    # Verificar si ya existe
    cursor.execute("SELECT id FROM attendances WHERE id_credencial = %s AND id_evento = %s", 
                  (id_credencial, id_evento))
    if cursor.fetchone():
        conn.close()
        return None
    
    attendance_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    cursor.execute('''
        INSERT INTO attendances (id, id_credencial, id_evento, hora_registro, validado)
        VALUES (%s, %s, %s, %s, %s)
    ''', (attendance_id, id_credencial, id_evento, now, 0))
    conn.commit()
    
    cursor.execute("SELECT * FROM attendances WHERE id = %s", (attendance_id,))
    new_attendance = row_to_dict(cursor.fetchone())
    conn.close()
    new_attendance['validado'] = bool(new_attendance['validado'])
    return new_attendance

def validate_attendance(attendance_id, validado):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE attendances SET validado = %s WHERE id = %s", 
                  (1 if validado else 0, attendance_id))
    conn.commit()
    
    cursor.execute("SELECT * FROM attendances WHERE id = %s", (attendance_id,))
    attendance = row_to_dict(cursor.fetchone())
    conn.close()
    if attendance:
        attendance['validado'] = bool(attendance['validado'])
    return attendance

# ==================== PRE-REGISTROS ====================

def get_event_pre_registros(event_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM pre_registros WHERE id_evento = %s ORDER BY fecha_registro DESC", (event_id,))
    pre_registros = rows_to_list(cursor.fetchall())
    conn.close()
    return pre_registros

def create_pre_registro(id_evento, id_estudiante, matricula):
    conn = get_connection()
    cursor = conn.cursor()
    
    # Verificar si ya existe
    cursor.execute("SELECT id FROM pre_registros WHERE id_evento = %s AND matricula = %s", 
                  (id_evento, matricula))
    if cursor.fetchone():
        conn.close()
        return None
    
    pre_registro_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    cursor.execute('''
        INSERT INTO pre_registros (id, id_evento, id_estudiante, matricula, fecha_registro)
        VALUES (%s, %s, %s, %s, %s)
    ''', (pre_registro_id, id_evento, id_estudiante, matricula, now))
    conn.commit()
    
    cursor.execute("SELECT * FROM pre_registros WHERE id = %s", (pre_registro_id,))
    new_pre_registro = row_to_dict(cursor.fetchone())
    conn.close()
    return new_pre_registro

def get_student_pre_registros_db(student_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM pre_registros WHERE id_estudiante = %s ORDER BY fecha_registro DESC", (student_id,))
    pre_registros = rows_to_list(cursor.fetchall())
    conn.close()
    return pre_registros

# ==================== ESTUDIANTES ====================

def get_all_students():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students ORDER BY matricula")
    students = rows_to_list(cursor.fetchall())
    conn.close()
    return students

def get_student_by_matricula(matricula):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students WHERE matricula = %s", (matricula,))
    student = cursor.fetchone()
    conn.close()
    return row_to_dict(student) if student else None

def create_student(student_data):
    conn = get_connection()
    cursor = conn.cursor()
    
    # Verificar si ya existe
    cursor.execute("SELECT id FROM students WHERE matricula = %s", (student_data['matricula'],))
    if cursor.fetchone():
        conn.close()
        return None
    
    student_id = str(uuid.uuid4())
    
    cursor.execute('''
        INSERT INTO students (id, matricula, nombre, carrera, semestre, email)
        VALUES (%s, %s, %s, %s, %s, %s)
    ''', (
        student_id, student_data['matricula'], student_data['nombre'],
        student_data.get('carrera'), student_data.get('semestre'),
        student_data.get('email')
    ))
    conn.commit()
    
    cursor.execute("SELECT * FROM students WHERE id = %s", (student_id,))
    new_student = row_to_dict(cursor.fetchone())
    conn.close()
    return new_student

def import_students_bulk(students_list):
    conn = get_connection()
    cursor = conn.cursor()
    imported_count = 0
    
    for student_data in students_list:
        try:
            # Verificar si ya existe
            cursor.execute("SELECT id FROM students WHERE matricula = %s", (student_data['matricula'],))
            if not cursor.fetchone():
                student_id = str(uuid.uuid4())
                cursor.execute('''
                    INSERT INTO students (id, matricula, nombre, carrera, semestre, email)
                    VALUES (%s, %s, %s, %s, %s, %s)
                ''', (
                    student_id, student_data['matricula'], student_data['nombre'],
                    student_data.get('carrera'), student_data.get('semestre'),
                    student_data.get('email')
                ))
                imported_count += 1
        except Exception as e:
            print(f"Error importando estudiante {student_data.get('matricula')}: {e}")
    
    conn.commit()
    conn.close()
    return imported_count

# ==================== ESTADÍSTICAS ====================

def get_event_statistics(event_id):
    conn = get_connection()
    cursor = conn.cursor()
    
    # Obtener evento
    cursor.execute("SELECT * FROM events WHERE id = %s", (event_id,))
    event = row_to_dict(cursor.fetchone())
    if not event:
        conn.close()
        return None
    
    # Contar asistencias
    cursor.execute("SELECT COUNT(*) as total FROM attendances WHERE id_evento = %s", (event_id,))
    total_attendances = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) as validated FROM attendances WHERE id_evento = %s AND validado = 1", (event_id,))
    validated_attendances = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        "event_id": event_id,
        "event_name": event["nombre"],
        "total_attendances": total_attendances,
        "validated_attendances": validated_attendances,
        "pending_validation": total_attendances - validated_attendances,
        "capacity_max": event["capacidad_maxima"],
        "capacity_used_percentage": (total_attendances / event["capacidad_maxima"] * 100) if event["capacidad_maxima"] else None
    }
