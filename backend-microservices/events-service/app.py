from fastapi import FastAPI, HTTPException, Depends, status, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import os
import uuid
import httpx
import shutil
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader
from db_helpers import *

app = FastAPI(title="Events Service - Sistema de Asistencias")

# Cargar variables de entorno desde la raíz del proyecto
ENV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
load_dotenv(dotenv_path=ENV_PATH)

# Configurar CORS dinámicamente
allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "*")
if allowed_origins_str == "*":
    allowed_origins = ["*"]
else:
    allowed_origins = [origin.strip() for origin in allowed_origins_str.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()
USERS_SERVICE_URL = os.getenv("USERS_SERVICE_URL", "http://localhost:8101")

# Crear carpeta para imágenes locales (ya no usada en nube) y montar como estática
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads", "images")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "uploads")), name="uploads")

# Configuración de Cloudinary
CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

if CLOUDINARY_CLOUD_NAME and CLOUDINARY_API_KEY and CLOUDINARY_API_SECRET:
    cloudinary.config(
        cloud_name=CLOUDINARY_CLOUD_NAME,
        api_key=CLOUDINARY_API_KEY,
        api_secret=CLOUDINARY_API_SECRET,
    )
    print(f"✓ Cloudinary configurado: {CLOUDINARY_CLOUD_NAME}")
else:
    print("⚠ Cloudinary no configurado. Las imágenes no se podrán subir a la nube.")

# ==================== MODELOS ====================

class EventCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    fecha_hora_inicio: str
    fecha_hora_fin: Optional[str] = None
    ubicacion: Optional[str] = None
    capacidad_maxima: Optional[int] = None
    imagen_url: Optional[str] = None

class EventUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    fecha_hora_inicio: Optional[str] = None
    fecha_hora_fin: Optional[str] = None
    ubicacion: Optional[str] = None
    capacidad_maxima: Optional[int] = None
    estado: Optional[str] = None
    imagen_url: Optional[str] = None

class Event(BaseModel):
    id: str
    nombre: str
    descripcion: Optional[str]
    fecha_hora_inicio: str
    fecha_hora_fin: Optional[str]
    ubicacion: Optional[str]
    capacidad_maxima: Optional[int]
    estado: str
    organizador_id: str
    created_at: str
    updated_at: str
    imagen_url: Optional[str] = None

class AttendanceCreate(BaseModel):
    id_credencial: str
    id_evento: str

class Student(BaseModel):
    id: Optional[str] = None
    matricula: str
    nombre: str
    carrera: Optional[str] = None
    semestre: Optional[int] = None
    email: Optional[str] = None

class Attendance(BaseModel):
    id: str
    id_credencial: str
    id_evento: str
    hora_registro: str
    validado: bool
    estudiante: Optional[Student] = None

class AttendanceValidation(BaseModel):
    validado: bool

class PreRegistroCreate(BaseModel):
    id_evento: str
    id_estudiante: str
    matricula: str

class PreRegistro(BaseModel):
    id: str
    id_evento: str
    id_estudiante: str
    matricula: str
    fecha_registro: str

class StudentCreate(BaseModel):
    matricula: str
    nombre: str
    carrera: Optional[str] = None
    semestre: Optional[int] = None
    email: Optional[str] = None

# ==================== AUTENTICACIÓN ====================

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{USERS_SERVICE_URL}/api/users/verify-token",
                headers={"Authorization": f"Bearer {credentials.credentials}"}
            )
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token inválido"
                )
    except httpx.RequestError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Servicio de usuarios no disponible"
        )

# ==================== EVENTOS ====================

@app.post("/api/events", response_model=Event, status_code=status.HTTP_201_CREATED)
def create_event(event: EventCreate, token_data: dict = Depends(verify_token)):
    new_event = create_event_db(event, token_data["user_id"])
    return new_event

@app.get("/api/events", response_model=List[Event])
def get_events(estado: Optional[str] = None, token_data: dict = Depends(verify_token)):
    events = get_all_events(estado)
    return events

@app.get("/api/events/{event_id}", response_model=Event)
def get_event(event_id: str, token_data: dict = Depends(verify_token)):
    event = get_event_by_id(event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evento no encontrado")
    return event

@app.put("/api/events/{event_id}", response_model=Event)
def update_event_endpoint(event_id: str, event_update: EventUpdate, token_data: dict = Depends(verify_token)):
    event = get_event_by_id(event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evento no encontrado")
    
    if event["organizador_id"] != token_data["user_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos para editar este evento")
    
    updated_event = update_event(event_id, event_update)
    return updated_event

@app.delete("/api/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event_endpoint(event_id: str, token_data: dict = Depends(verify_token)):
    event = get_event_by_id(event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evento no encontrado")
    
    # Admin puede borrar cualquier evento, otros solo los suyos
    if token_data.get("role") != "admin" and event["organizador_id"] != token_data["user_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos para eliminar este evento")
    
    delete_event(event_id)
    return None

# ==================== ASISTENCIAS ====================

@app.post("/api/attendances", response_model=Attendance, status_code=status.HTTP_201_CREATED)
def register_attendance(attendance: AttendanceCreate, token_data: dict = Depends(verify_token)):
    # Validar formato de matrícula (5 dígitos)
    if not attendance.id_credencial.isdigit() or len(attendance.id_credencial) != 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="La matrícula debe tener exactamente 5 dígitos numéricos"
        )
    
    event = get_event_by_id(attendance.id_evento)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evento no encontrado")
    
    # Solo admin puede registrar asistencias en eventos finalizados
    if event["estado"] != "activo":
        if token_data.get("role") != "admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo el administrador puede registrar asistencias en eventos finalizados")
    
    # Verificar capacidad
    if event["capacidad_maxima"]:
        current_attendances = get_event_attendances(attendance.id_evento)
        if len(current_attendances) >= event["capacidad_maxima"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Capacidad máxima del evento alcanzada")
    
    new_attendance = create_attendance(attendance.id_credencial, attendance.id_evento)
    if not new_attendance:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Asistencia ya registrada para este estudiante")
    
    return new_attendance

@app.get("/api/events/{event_id}/attendances", response_model=List[Attendance])
def get_attendances_endpoint(event_id: str, token_data: dict = Depends(verify_token)):
    event = get_event_by_id(event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evento no encontrado")
    
    attendances = get_event_attendances(event_id)
    return attendances

@app.put("/api/attendances/{attendance_id}/validate", response_model=Attendance)
def validate_attendance_endpoint(attendance_id: str, validation: AttendanceValidation, token_data: dict = Depends(verify_token)):
    attendance = validate_attendance(attendance_id, validation.validado)
    if not attendance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asistencia no encontrada")
    return attendance

# ==================== PRE-REGISTROS ====================

@app.post("/api/pre-registros", response_model=PreRegistro, status_code=status.HTTP_201_CREATED)
def create_pre_registro_endpoint(pre_registro: PreRegistroCreate, token_data: dict = Depends(verify_token)):
    event = get_event_by_id(pre_registro.id_evento)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evento no encontrado")
    
    # No permitir pre-registros en eventos finalizados
    if event["estado"] == "finalizado":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se pueden hacer pre-registros en eventos finalizados")
    
    # Validar formato de matrícula
    if not pre_registro.matricula.isdigit() or len(pre_registro.matricula) != 5:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La matrícula debe tener exactamente 5 dígitos")
    
    new_pre_registro = create_pre_registro(pre_registro.id_evento, pre_registro.id_estudiante, pre_registro.matricula)
    if not new_pre_registro:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ya está pre-registrado en este evento")
    
    return new_pre_registro

@app.get("/api/events/{event_id}/pre-registros")
def get_pre_registros_endpoint(event_id: str, token_data: dict = Depends(verify_token)):
    pre_registros = get_event_pre_registros(event_id)
    return pre_registros

@app.get("/api/pre-registros/student/{student_id}")
def get_student_pre_registros(student_id: str, token_data: dict = Depends(verify_token)):
    pre_registros = get_student_pre_registros_db(student_id)
    
    # Enriquecer con información del evento
    result = []
    for pre_reg in pre_registros:
        event = get_event_by_id(pre_reg["id_evento"])
        if event:
            result.append({
                **pre_reg,
                "evento_nombre": event["nombre"],
                "evento_fecha": event["fecha_hora_inicio"],
                "evento_ubicacion": event.get("ubicacion", "N/A")
            })
    
    return result

# ==================== ESTUDIANTES ====================

@app.get("/api/students")
def get_students_endpoint(token_data: dict = Depends(verify_token)):
    students = get_all_students()
    return students

@app.get("/api/students/search/{matricula}")
def search_student_endpoint(matricula: str, token_data: dict = Depends(verify_token)):
    student = get_student_by_matricula(matricula)
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Estudiante no encontrado en la base de datos")
    return student

@app.post("/api/students/import-excel")
def import_students_from_excel(token_data: dict = Depends(verify_token)):
    try:
        import pandas as pd
    except ImportError:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Pandas no está instalado")
    
    excel_path = "../../alumnos.xlsx"
    if not os.path.exists(excel_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Archivo alumnos.xlsx no encontrado")
    
    try:
        df = pd.read_excel(excel_path)
        df.columns = df.columns.str.lower().str.strip()
        
        students_list = []
        for _, row in df.iterrows():
            matricula = str(row.get('matricula') or row.get('matrícula', ''))
            nombre = str(row.get('nombre', ''))
            
            if not matricula or not nombre:
                continue
            
            students_list.append({
                'matricula': matricula,
                'nombre': nombre,
                'carrera': str(row.get('carrera', '')),
                'semestre': int(row.get('semestre', 0)) if pd.notna(row.get('semestre')) else None,
                'email': str(row.get('email', '')) if pd.notna(row.get('email')) else None
            })
        
        imported_count = import_students_bulk(students_list)
        total_students = len(get_all_students())
        
        return {"message": f"Se importaron {imported_count} estudiantes", "total_students": total_students}
    
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error al importar: {str(e)}")

# ==================== ESTADÍSTICAS ====================

@app.get("/api/events/{event_id}/statistics")
def get_statistics_endpoint(event_id: str, token_data: dict = Depends(verify_token)):
    stats = get_event_statistics(event_id)
    if not stats:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evento no encontrado")
    return stats

@app.post("/api/events/{event_id}/finalize")
def finalize_event_endpoint(event_id: str, token_data: dict = Depends(verify_token)):
    event = get_event_by_id(event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evento no encontrado")
    
    # Solo el organizador o un admin pueden finalizar el evento
    if event["organizador_id"] != token_data["user_id"] and token_data.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos para finalizar este evento")
    
    # Usar transacción para garantizar atomicidad
    from database import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Actualizar estado del evento
        cursor.execute(
            "UPDATE events SET estado = %s, updated_at = %s WHERE id = %s",
            ("finalizado", datetime.now().isoformat(), event_id)
        )
        
        # Validar todas las asistencias
        cursor.execute(
            "UPDATE attendances SET validado = %s WHERE id_evento = %s",
            (1, event_id)
        )
        
        conn.commit()
        
        # Obtener evento actualizado
        cursor.execute("SELECT * FROM events WHERE id = %s", (event_id,))
        from database import row_to_dict
        updated_event = row_to_dict(cursor.fetchone())
        
        conn.close()
        
        return {"message": "Evento finalizado y asistencias validadas", "event": updated_event}
        
    except Exception as e:
        conn.rollback()
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al finalizar evento: {str(e)}"
        )

# ==================== IMÁGENES ====================

@app.post("/api/events/upload-image")
async def upload_image(file: UploadFile = File(...), token_data: dict = Depends(verify_token)):
    # Verificar que Cloudinary esté configurado
    if not CLOUDINARY_CLOUD_NAME or not CLOUDINARY_API_KEY or not CLOUDINARY_API_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cloudinary no está configurado. Configure las variables de entorno CLOUDINARY_*"
        )
    
    # Validar tipo de archivo
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    file_extension = os.path.splitext(file.filename)[1].lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tipo de archivo no permitido")
    
    # Subir a Cloudinary
    try:
        upload_result = cloudinary.uploader.upload(
            file.file,
            folder="events",
            resource_type="image"
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error al subir imagen: {str(e)}")
    
    secure_url = upload_result.get("secure_url")
    public_id = upload_result.get("public_id")
    if not secure_url:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="No se pudo obtener URL de imagen")
    
    # Retornar URL absoluta alojada en Cloudinary
    return {"imagen_url": secure_url, "public_id": public_id}

# ==================== ROOT ====================

@app.get("/")
def root():
    return {"service": "Events Service", "version": "2.0", "status": "running", "database": "SQL"}

@app.get("/health")
def health_check():
    """Health check endpoint para monitoreo"""
    health_status = {
        "status": "healthy",
        "service": "Events Service",
        "checks": {}
    }
    
    # Verificar base de datos
    try:
        from database import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        conn.close()
        health_status["checks"]["database"] = "connected"
        health_status["database_type"] = "PostgreSQL" if os.getenv("DATABASE_URL", "").startswith("postgres") else "SQLite"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = f"error: {str(e)}"
    
    # Verificar Cloudinary
    if CLOUDINARY_CLOUD_NAME and CLOUDINARY_API_KEY and CLOUDINARY_API_SECRET:
        health_status["checks"]["cloudinary"] = "configured"
    else:
        health_status["checks"]["cloudinary"] = "not_configured"
    
    return health_status

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8102))
    uvicorn.run(app, host="0.0.0.0", port=port)
