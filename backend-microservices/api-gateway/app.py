from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse, Response
import httpx
from typing import Optional
import os
from dotenv import load_dotenv

app = FastAPI(title="API Gateway - Sistema de Asistencias")

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

SERVICES = {
    "users": os.getenv("USERS_SERVICE_URL", "http://localhost:8101"),
    "events": os.getenv("EVENTS_SERVICE_URL", "http://localhost:8102"),
    "reports": os.getenv("REPORTS_SERVICE_URL", "http://localhost:8103")
}

async def proxy_request(service_url: str, path: str, request: Request):
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            headers = dict(request.headers)
            headers.pop("host", None)
            
            url = f"{service_url}{path}"
            print(f"[Gateway] {request.method} {url}")
            
            if request.method == "OPTIONS":
                # Preflight CORS request: respond OK and let CORSMiddleware append headers
                return JSONResponse(content={}, status_code=200)
            elif request.method == "GET":
                response = await client.get(url, headers=headers, params=request.query_params)
            elif request.method == "POST":
                body = await request.body()
                print(f"[Gateway] Body length: {len(body)}")
                response = await client.post(url, headers=headers, content=body)
            elif request.method == "PUT":
                body = await request.body()
                response = await client.put(url, headers=headers, content=body)
            elif request.method == "DELETE":
                response = await client.delete(url, headers=headers)
            else:
                raise HTTPException(status_code=405, detail="Método no permitido")
            
            content_type = response.headers.get("content-type", "")
            
            # Manejar CSV
            if content_type.startswith("text/csv"):
                return StreamingResponse(
                    iter([response.content]),
                    media_type="text/csv",
                    headers=dict(response.headers)
                )
            
            # Manejar PDF
            if content_type.startswith("application/pdf"):
                return Response(
                    content=response.content,
                    media_type="application/pdf",
                    headers={
                        "Content-Disposition": response.headers.get("content-disposition", "attachment; filename=reporte.pdf")
                    }
                )
            
            # Manejar imágenes
            if content_type.startswith("image/"):
                return Response(
                    content=response.content,
                    media_type=content_type,
                    headers={
                        "Cache-Control": "public, max-age=31536000"
                    }
                )
            
            # Intentar parsear JSON, si falla devolver contenido raw
            try:
                content = response.json() if response.text else {}
            except Exception:
                content = {"detail": response.text or "Sin contenido"}
            
            # Filtrar headers problemáticos
            response_headers = dict(response.headers)
            response_headers.pop("content-length", None)
            response_headers.pop("content-encoding", None)
            response_headers.pop("transfer-encoding", None)
            
            return JSONResponse(
                content=content,
                status_code=response.status_code
            )
        
        except httpx.RequestError as e:
            print(f"[Gateway] Error: {str(e)}")
            raise HTTPException(
                status_code=503,
                detail=f"Servicio no disponible: {str(e)}"
            )

@app.api_route("/api/users/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
async def users_proxy(path: str, request: Request):
    return await proxy_request(SERVICES["users"], f"/api/users/{path}", request)

@app.api_route("/api/events/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
async def events_proxy(path: str, request: Request):
    return await proxy_request(SERVICES["events"], f"/api/events/{path}", request)

@app.api_route("/api/events", methods=["GET", "POST", "OPTIONS"])
async def events_root_proxy(request: Request):
    return await proxy_request(SERVICES["events"], "/api/events", request)

@app.api_route("/api/attendances/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
async def attendances_proxy(path: str, request: Request):
    return await proxy_request(SERVICES["events"], f"/api/attendances/{path}", request)

@app.api_route("/api/attendances", methods=["GET", "POST", "OPTIONS"])
async def attendances_root_proxy(request: Request):
    return await proxy_request(SERVICES["events"], "/api/attendances", request)

@app.api_route("/api/reports/export/event/{event_id}/pdf", methods=["GET", "OPTIONS"])
async def reports_pdf_proxy(event_id: str, request: Request):
    return await proxy_request(SERVICES["reports"], f"/api/reports/export/event/{event_id}/pdf", request)

@app.api_route("/api/reports/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
async def reports_proxy(path: str, request: Request):
    return await proxy_request(SERVICES["reports"], f"/api/reports/{path}", request)

@app.api_route("/api/pre-registros/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
async def pre_registros_proxy(path: str, request: Request):
    return await proxy_request(SERVICES["events"], f"/api/pre-registros/{path}", request)

@app.api_route("/api/pre-registros", methods=["GET", "POST", "OPTIONS"])
async def pre_registros_root_proxy(request: Request):
    return await proxy_request(SERVICES["events"], "/api/pre-registros", request)

@app.api_route("/api/students/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
async def students_proxy(path: str, request: Request):
    return await proxy_request(SERVICES["events"], f"/api/students/{path}", request)

@app.api_route("/api/students", methods=["GET", "POST", "OPTIONS"])
async def students_root_proxy(request: Request):
    return await proxy_request(SERVICES["events"], "/api/students", request)

@app.api_route("/api/uploads/{path:path}", methods=["GET"])
async def api_uploads_proxy(path: str, request: Request):
    return await proxy_request(SERVICES["events"], f"/uploads/{path}", request)

@app.api_route("/uploads/{path:path}", methods=["GET"])
async def uploads_proxy(path: str, request: Request):
    return await proxy_request(SERVICES["events"], f"/uploads/{path}", request)

@app.get("/health")
async def health_check():
    health_status = {}
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        for service_name, service_url in SERVICES.items():
            try:
                response = await client.get(f"{service_url}/")
                health_status[service_name] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "response_time": response.elapsed.total_seconds()
                }
            except Exception as e:
                health_status[service_name] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
    
    all_healthy = all(s["status"] == "healthy" for s in health_status.values())
    
    return {
        "gateway": "healthy",
        "services": health_status,
        "overall_status": "healthy" if all_healthy else "degraded"
    }

@app.get("/")
def root():
    return {
        "service": "API Gateway",
        "version": "1.0",
        "status": "running",
        "available_services": list(SERVICES.keys())
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8100))
    uvicorn.run(app, host="0.0.0.0", port=port)
