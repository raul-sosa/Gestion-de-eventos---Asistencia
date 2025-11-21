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
import requests

app = FastAPI(title="Reports Service - Sistema de Asistencias")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()
USERS_SERVICE_URL = "http://localhost:8101"
EVENTS_SERVICE_URL = "http://localhost:8102"

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

def get_events_data(token: str):
    try:
        response = requests.get(
            f"{EVENTS_SERVICE_URL}/api/events",
            headers={"Authorization": f"Bearer {token}"}
        )
        if response.status_code == 200:
            return response.json()
        return []
    except requests.RequestException:
        return []

def get_event_attendances(event_id: str, token: str):
    try:
        response = requests.get(
            f"{EVENTS_SERVICE_URL}/api/events/{event_id}/attendances",
            headers={"Authorization": f"Bearer {token}"}
        )
        if response.status_code == 200:
            return response.json()
        return []
    except requests.RequestException:
        return []

@app.post("/api/reports/attendances", response_model=List[AttendanceReport])
def get_attendances_report(
    filters: ReportFilters,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    token_data: dict = Depends(verify_token)
):
    token = credentials.credentials
    events = get_events_data(token)
    
    all_attendances = []
    
    if filters.event_id:
        target_events = [e for e in events if e["id"] == filters.event_id]
    else:
        target_events = events
    
    for event in target_events:
        attendances = get_event_attendances(event["id"], token)
        
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
def get_events_report(
    estado: Optional[str] = Query(None),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    token_data: dict = Depends(verify_token)
):
    token = credentials.credentials
    events = get_events_data(token)
    
    if estado:
        events = [e for e in events if e["estado"] == estado]
    
    events_report = []
    for event in events:
        attendances = get_event_attendances(event["id"], token)
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
def export_attendances_csv(
    filters: ReportFilters,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    token_data: dict = Depends(verify_token)
):
    attendances = get_attendances_report(filters, credentials, token_data)
    
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
def export_attendances_json(
    filters: ReportFilters,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    token_data: dict = Depends(verify_token)
):
    attendances = get_attendances_report(filters, credentials, token_data)
    
    json_data = json.dumps(attendances, indent=2, ensure_ascii=False)
    
    return StreamingResponse(
        iter([json_data]),
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=reporte_asistencias_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        }
    )

@app.get("/api/reports/export/events/csv")
def export_events_csv(
    estado: Optional[str] = Query(None),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    token_data: dict = Depends(verify_token)
):
    events = get_events_report(estado, credentials, token_data)
    
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
def get_global_statistics(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    token_data: dict = Depends(verify_token)
):
    token = credentials.credentials
    events = get_events_data(token)
    
    total_events = len(events)
    active_events = len([e for e in events if e["estado"] == "activo"])
    finalized_events = len([e for e in events if e["estado"] == "finalizado"])
    
    total_attendances = 0
    total_validated = 0
    
    for event in events:
        attendances = get_event_attendances(event["id"], token)
        total_attendances += len(attendances)
        total_validated += len([a for a in attendances if a["validado"]])
    
    return {
        "total_events": total_events,
        "active_events": active_events,
        "finalized_events": finalized_events,
        "total_attendances": total_attendances,
        "validated_attendances": total_validated,
        "pending_validation": total_attendances - total_validated,
        "average_attendances_per_event": round(total_attendances / total_events, 2) if total_events > 0 else 0
    }

@app.get("/api/reports/export/event/{event_id}/pdf")
def export_event_pdf(
    event_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    token_data: dict = Depends(verify_token)
):
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.units import inch
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ReportLab no está instalado"
        )
    
    token = credentials.credentials
    events = get_events_data(token)
    event = next((e for e in events if e["id"] == event_id), None)
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento no encontrado"
        )
    
    attendances = get_event_attendances(event_id, token)
    
    # Crear PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Título
    title = Paragraph(f"<b>Reporte de Asistencia - {event['nombre']}</b>", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 0.3*inch))
    
    # Información del evento
    info_data = [
        ["Evento:", event['nombre']],
        ["Fecha Inicio:", event['fecha_hora_inicio']],
        ["Ubicación:", event.get('ubicacion', 'N/A')],
        ["Estado:", event['estado']],
        ["Total Asistencias:", str(len(attendances))],
        ["Validadas:", str(len([a for a in attendances if a['validado']]))],
    ]
    
    info_table = Table(info_data, colWidths=[2*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.grey),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(info_table)
    elements.append(Spacer(1, 0.5*inch))
    
    # Tabla de asistencias
    if attendances:
        elements.append(Paragraph("<b>Lista de Asistencias</b>", styles['Heading2']))
        elements.append(Spacer(1, 0.2*inch))
        
        attendance_data = [["#", "ID Credencial", "Hora Registro", "Estado"]]
        for idx, att in enumerate(attendances, 1):
            attendance_data.append([
                str(idx),
                att['id_credencial'],
                att['hora_registro'][:19],
                "Validado" if att['validado'] else "Pendiente"
            ])
        
        attendance_table = Table(attendance_data, colWidths=[0.5*inch, 2*inch, 2.5*inch, 1.5*inch])
        attendance_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.beige, colors.white])
        ]))
        
        elements.append(attendance_table)
    
    doc.build(elements)
    buffer.seek(0)
    pdf_bytes = buffer.getvalue()
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=reporte_{event['nombre'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf",
            "Content-Length": str(len(pdf_bytes))
        }
    )

@app.get("/")
def root():
    return {"service": "Reports Service", "version": "1.0", "status": "running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8103)
