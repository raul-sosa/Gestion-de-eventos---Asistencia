from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import json
import os
import uuid
import requests

app = FastAPI(title="Events Service - Sistema de Asistencias")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()
USERS_SERVICE_URL = "http://localhost:8101"

DB_FILE = "events_db.json"

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

class Attendance(BaseModel):
    id: str
    id_credencial: str
    id_evento: str
    hora_registro: str
    validado: bool

class AttendanceValidation(BaseModel):
    validado: bool

def load_database():
    if not os.path.exists(DB_FILE):
        initial_data = {
            "events": [],
            "attendances": [],
            "pre_registros": [],
            "students": []
        }
        save_database(initial_data)
        return initial_data
    
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        # Asegurar que existan las nuevas claves
        if "pre_registros" not in data:
            data["pre_registros"] = []
        if "students" not in data:
            data["students"] = []
        return data

def save_database(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        response = requests.post(
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
    except requests.RequestException:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Servicio de usuarios no disponible"
        )

@app.post("/api/events", response_model=Event, status_code=status.HTTP_201_CREATED)
def create_event(event: EventCreate, token_data: dict = Depends(verify_token)):
    db = load_database()
    
    new_event = {
        "id": str(uuid.uuid4()),
        "nombre": event.nombre,
        "descripcion": event.descripcion,
        "fecha_hora_inicio": event.fecha_hora_inicio,
        "fecha_hora_fin": event.fecha_hora_fin,
        "ubicacion": event.ubicacion,
        "capacidad_maxima": event.capacidad_maxima,
        "estado": "activo",
        "organizador_id": token_data["user_id"],
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "imagen_url": event.imagen_url
    }
    
    db["events"].append(new_event)
    save_database(db)
    
    return new_event

@app.get("/api/events", response_model=List[Event])
def get_events(
    estado: Optional[str] = None,
    token_data: dict = Depends(verify_token)
):
    db = load_database()
    events = db["events"]
    
    if estado:
        events = [e for e in events if e["estado"] == estado]
    
    return events

@app.get("/api/events/{event_id}", response_model=Event)
def get_event(event_id: str, token_data: dict = Depends(verify_token)):
    db = load_database()
    event = next((e for e in db["events"] if e["id"] == event_id), None)
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento no encontrado"
        )
    
    return event

@app.put("/api/events/{event_id}", response_model=Event)
def update_event(
    event_id: str,
    event_update: EventUpdate,
    token_data: dict = Depends(verify_token)
):
    db = load_database()
    event_index = next((i for i, e in enumerate(db["events"]) if e["id"] == event_id), None)
    
    if event_index is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento no encontrado"
        )
    
    event = db["events"][event_index]
    
    if event["organizador_id"] != token_data["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para editar este evento"
        )
    
    update_data = event_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        event[key] = value
    
    event["updated_at"] = datetime.now().isoformat()
    db["events"][event_index] = event
    save_database(db)
    
    return event

@app.delete("/api/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(event_id: str, token_data: dict = Depends(verify_token)):
    db = load_database()
    event_index = next((i for i, e in enumerate(db["events"]) if e["id"] == event_id), None)
    
    if event_index is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento no encontrado"
        )
    
    event = db["events"][event_index]
    
    if event["organizador_id"] != token_data["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para eliminar este evento"
        )
    
    db["events"].pop(event_index)
    
    db["attendances"] = [a for a in db["attendances"] if a["id_evento"] != event_id]
    
    save_database(db)
    return None

@app.post("/api/attendances", response_model=Attendance, status_code=status.HTTP_201_CREATED)
def register_attendance(attendance: AttendanceCreate, token_data: dict = Depends(verify_token)):
    db = load_database()
    
    event = next((e for e in db["events"] if e["id"] == attendance.id_evento), None)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento no encontrado"
        )
    
    if event["estado"] != "activo":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El evento no está activo"
        )
    
    existing = next((a for a in db["attendances"] 
                    if a["id_credencial"] == attendance.id_credencial 
                    and a["id_evento"] == attendance.id_evento), None)
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Asistencia ya registrada para este estudiante"
        )
    
    if event["capacidad_maxima"]:
        current_attendances = len([a for a in db["attendances"] if a["id_evento"] == attendance.id_evento])
        if current_attendances >= event["capacidad_maxima"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Capacidad máxima del evento alcanzada"
            )
    
    new_attendance = {
        "id": str(uuid.uuid4()),
        "id_credencial": attendance.id_credencial,
        "id_evento": attendance.id_evento,
        "hora_registro": datetime.now().isoformat(),
        "validado": False
    }
    
    db["attendances"].append(new_attendance)
    save_database(db)
    
    return new_attendance

@app.get("/api/events/{event_id}/attendances", response_model=List[Attendance])
def get_event_attendances(event_id: str, token_data: dict = Depends(verify_token)):
    db = load_database()
    
    event = next((e for e in db["events"] if e["id"] == event_id), None)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento no encontrado"
        )
    
    attendances = [a for a in db["attendances"] if a["id_evento"] == event_id]
    return attendances

@app.put("/api/attendances/{attendance_id}/validate", response_model=Attendance)
def validate_attendance(
    attendance_id: str,
    validation: AttendanceValidation,
    token_data: dict = Depends(verify_token)
):
    db = load_database()
    attendance_index = next((i for i, a in enumerate(db["attendances"]) if a["id"] == attendance_id), None)
    
    if attendance_index is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asistencia no encontrada"
        )
    
    db["attendances"][attendance_index]["validado"] = validation.validado
    save_database(db)
    
    return db["attendances"][attendance_index]

@app.post("/api/events/{event_id}/finalize")
def finalize_event(event_id: str, token_data: dict = Depends(verify_token)):
    db = load_database()
    event_index = next((i for i, e in enumerate(db["events"]) if e["id"] == event_id), None)
    
    if event_index is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento no encontrado"
        )
    
    event = db["events"][event_index]
    
    if event["organizador_id"] != token_data["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para finalizar este evento"
        )
    
    event["estado"] = "finalizado"
    event["updated_at"] = datetime.now().isoformat()
    
    for i, attendance in enumerate(db["attendances"]):
        if attendance["id_evento"] == event_id:
            db["attendances"][i]["validado"] = True
    
    db["events"][event_index] = event
    save_database(db)
    
    return {"message": "Evento finalizado y asistencias validadas", "event": event}

@app.get("/api/events/{event_id}/statistics")
def get_event_statistics(event_id: str, token_data: dict = Depends(verify_token)):
    db = load_database()
    
    event = next((e for e in db["events"] if e["id"] == event_id), None)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento no encontrado"
        )
    
    attendances = [a for a in db["attendances"] if a["id_evento"] == event_id]
    validated = [a for a in attendances if a["validado"]]
    
    return {
        "event_id": event_id,
        "event_name": event["nombre"],
        "total_attendances": len(attendances),
        "validated_attendances": len(validated),
        "pending_validation": len(attendances) - len(validated),
        "capacity_max": event["capacidad_maxima"],
        "capacity_used_percentage": (len(attendances) / event["capacidad_maxima"] * 100) if event["capacidad_maxima"] else None
    }

class PreRegistroCreate(BaseModel):
    id_evento: str
    id_estudiante: str

class PreRegistro(BaseModel):
    id: str
    id_evento: str
    id_estudiante: str
    fecha_registro: str

class StudentCreate(BaseModel):
    matricula: str
    nombre: str
    carrera: Optional[str] = None
    semestre: Optional[int] = None
    email: Optional[str] = None

@app.post("/api/pre-registros", response_model=PreRegistro, status_code=status.HTTP_201_CREATED)
def create_pre_registro(pre_registro: PreRegistroCreate, token_data: dict = Depends(verify_token)):
    db = load_database()
    
    # Verificar que el evento existe
    event = next((e for e in db["events"] if e["id"] == pre_registro.id_evento), None)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento no encontrado"
        )
    
    # Verificar que no esté ya pre-registrado
    existing = next((p for p in db["pre_registros"] 
                    if p["id_evento"] == pre_registro.id_evento 
                    and p["id_estudiante"] == pre_registro.id_estudiante), None)
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya está pre-registrado en este evento"
        )
    
    new_pre_registro = {
        "id": str(uuid.uuid4()),
        "id_evento": pre_registro.id_evento,
        "id_estudiante": pre_registro.id_estudiante,
        "fecha_registro": datetime.now().isoformat()
    }
    
    db["pre_registros"].append(new_pre_registro)
    save_database(db)
    
    return new_pre_registro

@app.get("/api/events/{event_id}/pre-registros")
def get_event_pre_registros(event_id: str, token_data: dict = Depends(verify_token)):
    db = load_database()
    pre_registros = [p for p in db["pre_registros"] if p["id_evento"] == event_id]
    return pre_registros

@app.post("/api/students/import-excel")
def import_students_from_excel(token_data: dict = Depends(verify_token)):
    try:
        import pandas as pd
        import openpyxl
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Pandas u openpyxl no están instalados"
        )
    
    excel_path = "../../alumnos.xlsx"
    if not os.path.exists(excel_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Archivo alumnos.xlsx no encontrado en {excel_path}"
        )
    
    try:
        df = pd.read_excel(excel_path)
        
        # Normalizar nombres de columnas
        df.columns = df.columns.str.lower().str.strip()
        
        db = load_database()
        imported_count = 0
        
        for _, row in df.iterrows():
            matricula = str(row.get('matricula') or row.get('matrícula', ''))
            nombre = str(row.get('nombre', ''))
            
            if not matricula or not nombre:
                continue
            
            # Verificar si ya existe
            existing = next((s for s in db["students"] if s["matricula"] == matricula), None)
            if existing:
                continue
            
            student = {
                "id": str(uuid.uuid4()),
                "matricula": matricula,
                "nombre": nombre,
                "carrera": str(row.get('carrera', '')),
                "semestre": int(row.get('semestre', 0)) if pd.notna(row.get('semestre')) else None,
                "email": str(row.get('email', '')) if pd.notna(row.get('email')) else None
            }
            
            db["students"].append(student)
            imported_count += 1
        
        save_database(db)
        
        return {
            "message": f"Se importaron {imported_count} estudiantes",
            "total_students": len(db["students"])
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al importar: {str(e)}"
        )

@app.get("/api/students/search/{matricula}")
def search_student(matricula: str, token_data: dict = Depends(verify_token)):
    db = load_database()
    student = next((s for s in db["students"] if s["matricula"] == matricula), None)
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Estudiante no encontrado en la base de datos"
        )
    
    return student

@app.get("/api/students")
def get_all_students(token_data: dict = Depends(verify_token)):
    db = load_database()
    return db["students"]

@app.get("/")
def root():
    return {"service": "Events Service", "version": "1.0", "status": "running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8102)
