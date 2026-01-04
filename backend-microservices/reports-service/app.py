from fastapi import FastAPI, HTTPException, Depends, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import json
import io
import csv
import httpx
import sys
import os
from dotenv import load_dotenv

# Agregar path para importar database
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import get_connection

app = FastAPI(title="Reports Service - Sistema de Asistencias")

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
EVENTS_SERVICE_URL = os.getenv("EVENTS_SERVICE_URL", "http://localhost:8102")

class AttendanceReport(BaseModel):
    id: str
    id_credencial: str
    id_evento: str
    nombre_evento: str
    hora_registro: str
    validado: bool

class EventReport(BaseModel):
    id: str
    nombre: str
    descripcion: Optional[str]
    fecha_hora_inicio: str
    fecha_hora_fin: Optional[str]
    ubicacion: Optional[str]
    total_asistencias: int
    asistencias_validadas: int
    estado: str

class ReportFilters(BaseModel):
    event_id: Optional[str] = None
    fecha_inicio: Optional[str] = None
    fecha_fin: Optional[str] = None
    validado: Optional[bool] = None
    search_term: Optional[str] = None

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
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
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Timeout al verificar token"
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Servicio de usuarios no disponible: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado: {str(e)}"
        )

async def get_events_data(token: str):
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                f"{EVENTS_SERVICE_URL}/api/events",
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code == 200:
                return response.json()
            return []
    except (httpx.TimeoutException, httpx.RequestError, Exception) as e:
        print(f"Error obteniendo eventos: {str(e)}")
        return []

async def get_event_attendances(event_id: str, token: str):
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                f"{EVENTS_SERVICE_URL}/api/events/{event_id}/attendances",
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code == 200:
                return response.json()
            return []
    except (httpx.TimeoutException, httpx.RequestError, Exception) as e:
        print(f"Error obteniendo asistencias del evento {event_id}: {str(e)}")
        return []

@app.post("/api/reports/attendances", response_model=List[AttendanceReport])
async def get_attendances_report(
    filters: ReportFilters,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    token_data: dict = Depends(verify_token)
):
    token = credentials.credentials
    events = await get_events_data(token)
    
    all_attendances = []
    
    if filters.event_id:
        target_events = [e for e in events if e["id"] == filters.event_id]
    else:
        target_events = events
    
    for event in target_events:
        attendances = await get_event_attendances(event["id"], token)
        
        for attendance in attendances:
            attendance_report = {
                "id": attendance["id"],
                "id_credencial": attendance["id_credencial"],
                "id_evento": attendance["id_evento"],
                "nombre_evento": event["nombre"],
                "hora_registro": attendance["hora_registro"],
                "validado": attendance["validado"]
            }
            all_attendances.append(attendance_report)
    
    if filters.fecha_inicio:
        fecha_inicio = datetime.fromisoformat(filters.fecha_inicio)
        all_attendances = [
            a for a in all_attendances 
            if datetime.fromisoformat(a["hora_registro"]) >= fecha_inicio
        ]
    
    if filters.fecha_fin:
        fecha_fin = datetime.fromisoformat(filters.fecha_fin)
        all_attendances = [
            a for a in all_attendances 
            if datetime.fromisoformat(a["hora_registro"]) <= fecha_fin
        ]
    
    if filters.validado is not None:
        all_attendances = [a for a in all_attendances if a["validado"] == filters.validado]
    
    if filters.search_term:
        search_lower = filters.search_term.lower()
        all_attendances = [
            a for a in all_attendances 
            if search_lower in a["id_credencial"].lower() 
            or search_lower in a["nombre_evento"].lower()
        ]
    
    return all_attendances

@app.get("/api/reports/events", response_model=List[EventReport])
async def get_events_report(
    estado: Optional[str] = Query(None),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    token_data: dict = Depends(verify_token)
):
    token = credentials.credentials
    events = await get_events_data(token)
    
    if estado:
        events = [e for e in events if e["estado"] == estado]
    
    events_report = []
    for event in events:
        attendances = await get_event_attendances(event["id"], token)
        validated = [a for a in attendances if a["validado"]]
        
        event_report = {
            "id": event["id"],
            "nombre": event["nombre"],
            "descripcion": event.get("descripcion"),
            "fecha_hora_inicio": event["fecha_hora_inicio"],
            "fecha_hora_fin": event.get("fecha_hora_fin"),
            "ubicacion": event.get("ubicacion"),
            "total_asistencias": len(attendances),
            "asistencias_validadas": len(validated),
            "estado": event["estado"]
        }
        events_report.append(event_report)
    
    return events_report

@app.post("/api/reports/export/attendances/csv")
async def export_attendances_csv(
    filters: ReportFilters,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    token_data: dict = Depends(verify_token)
):
    attendances = await get_attendances_report(filters, credentials, token_data)
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        "ID Asistencia",
        "ID Credencial",
        "Evento",
        "Hora de Registro",
        "Validado"
    ])
    
    for attendance in attendances:
        writer.writerow([
            attendance["id"],
            attendance["id_credencial"],
            attendance["nombre_evento"],
            attendance["hora_registro"],
            "Sí" if attendance["validado"] else "No"
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=reporte_asistencias_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        }
    )

@app.post("/api/reports/export/attendances/json")
async def export_attendances_json(
    filters: ReportFilters,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    token_data: dict = Depends(verify_token)
):
    attendances = await get_attendances_report(filters, credentials, token_data)
    
    json_data = json.dumps(attendances, indent=2, ensure_ascii=False)
    
    return StreamingResponse(
        iter([json_data]),
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=reporte_asistencias_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        }
    )

@app.get("/api/reports/export/events/csv")
async def export_events_csv(
    estado: Optional[str] = Query(None),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    token_data: dict = Depends(verify_token)
):
    events = await get_events_report(estado, credentials, token_data)
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        "ID Evento",
        "Nombre",
        "Descripción",
        "Fecha Inicio",
        "Fecha Fin",
        "Ubicación",
        "Total Asistencias",
        "Asistencias Validadas",
        "Estado"
    ])
    
    for event in events:
        writer.writerow([
            event["id"],
            event["nombre"],
            event["descripcion"] or "",
            event["fecha_hora_inicio"],
            event["fecha_hora_fin"] or "",
            event["ubicacion"] or "",
            event["total_asistencias"],
            event["asistencias_validadas"],
            event["estado"]
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=reporte_eventos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        }
    )

@app.get("/api/reports/statistics/global")
async def get_global_statistics(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    token_data: dict = Depends(verify_token)
):
    token = credentials.credentials
    events = await get_events_data(token)
    
    total_events = len(events)
    active_events = len([e for e in events if e["estado"] == "activo"])
    finalized_events = len([e for e in events if e["estado"] == "finalizado"])
    
    total_attendances = 0
    total_pre_registros = 0
    
    # Obtener pre-registros de la base de datos
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM pre_registros")
    total_pre_registros = cursor.fetchone()[0]
    
    for event in events:
        attendances = await get_event_attendances(event["id"], token)
        total_attendances += len(attendances)
    
    conn.close()
    
    return {
        "total_events": total_events,
        "active_events": active_events,
        "finalized_events": finalized_events,
        "total_pre_registros": total_pre_registros,
        "total_attendances": total_attendances,
        "average_attendances_per_event": round(total_attendances / total_events, 2) if total_events > 0 else 0
    }

@app.get("/api/reports/export/event/{event_id}/pdf")
async def export_event_pdf(
    event_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    token_data: dict = Depends(verify_token)
):
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.units import inch
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ReportLab no está instalado"
        )
    
    token = credentials.credentials
    events = await get_events_data(token)
    event = next((e for e in events if e["id"] == event_id), None)
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento no encontrado"
        )
    
    attendances = await get_event_attendances(event_id, token)
    
    # Buscar información de estudiantes en la base de datos
    conn = get_connection()
    cursor = conn.cursor()
    
    # Crear PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Título
    title = Paragraph(f"<b>Reporte de Asistencia</b>", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 0.2*inch))
    
    # Información del evento
    event_info = Paragraph(f"<b>Evento:</b> {event['nombre']}<br/>"
                          f"<b>Fecha:</b> {event['fecha_hora_inicio']}<br/>"
                          f"<b>Ubicacion:</b> {event.get('ubicacion', 'N/A')}<br/>"
                          f"<b>Total Asistencias:</b> {len(attendances)}", styles['Normal'])
    elements.append(event_info)
    elements.append(Spacer(1, 0.3*inch))
    
    # Tabla de asistencias
    if attendances:
        elements.append(Paragraph("<b>Lista de Asistencias</b>", styles['Heading2']))
        elements.append(Spacer(1, 0.2*inch))
        
        attendance_data = [["#", "Matricula", "Nombre", "Carrera", "Hora"]]
        
        for idx, att in enumerate(attendances, 1):
            matricula = att['id_credencial']
            
            # Buscar estudiante en la base de datos
            cursor.execute("SELECT nombre, carrera FROM students WHERE matricula = %s", (matricula,))
            student_row = cursor.fetchone()
            
            if student_row:
                nombre = student_row[0] if student_row[0] else "N/A"
                carrera = student_row[1] if student_row[1] else "N/A"
            else:
                nombre = "No registrado"
                carrera = "N/A"
            
            attendance_data.append([
                str(idx),
                matricula,
                nombre,
                carrera,
                att['hora_registro'][:16]
            ])
        
        attendance_table = Table(attendance_data, colWidths=[0.4*inch, 1*inch, 2.2*inch, 1.8*inch, 1.2*inch])
        attendance_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F2F2F2')])
        ]))
        
        elements.append(attendance_table)
    else:
        elements.append(Paragraph("No hay asistencias registradas.", styles['Normal']))
    
    conn.close()
    
    doc.build(elements)
    buffer.seek(0)
    pdf_bytes = buffer.getvalue()
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=reporte_{event['nombre'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf"
        }
    )

@app.get("/")
def root():
    return {"service": "Reports Service", "version": "1.0", "status": "running"}

@app.get("/health")
async def health_check():
    """Health check endpoint para monitoreo"""
    health_status = {
        "status": "healthy",
        "service": "Reports Service",
        "checks": {}
    }
    
    # Verificar base de datos
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        conn.close()
        health_status["checks"]["database"] = "connected"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = f"error: {str(e)}"
    
    # Verificar conectividad con otros servicios
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{USERS_SERVICE_URL}/")
            health_status["checks"]["users_service"] = "reachable" if response.status_code == 200 else "unreachable"
    except:
        health_status["checks"]["users_service"] = "unreachable"
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{EVENTS_SERVICE_URL}/")
            health_status["checks"]["events_service"] = "reachable" if response.status_code == 200 else "unreachable"
    except:
        health_status["checks"]["events_service"] = "unreachable"
    
    return health_status

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8103))
    uvicorn.run(app, host="0.0.0.0", port=port)
