from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timedelta, timezone
import sys
import os
from dotenv import load_dotenv
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import get_connection, row_to_dict, rows_to_list, init_database
import uuid
import jwt
import bcrypt

app = FastAPI(title="Users Service - Sistema de Asistencias")

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

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480

# Inicializar base de datos solo en SQLite (en Postgres se asume gestionado en migración)
if not os.getenv("DATABASE_URL", "").startswith("postgres"):
    init_database()

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str
    role: str = "organizador"

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: str
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: str
    created_at: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None

def hash_password(password: str) -> str:
    """Hash password usando bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verificar password contra hash"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def ensure_default_users():
    """Asegura que existan los usuarios por defecto"""
    conn = get_connection()
    cursor = conn.cursor()
    
    default_users = [
        ("admin", "admin@eventos.com", "admin123", "Administrador", "admin"),
        ("encargado", "encargado@eventos.com", "encargado123", "Encargado de Asistencia", "encargado"),
        ("estudiante", "estudiante@eventos.com", "estudiante123", "Estudiante Prueba", "estudiante")
    ]
    
    for username, email, password, full_name, role in default_users:
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO users (id, username, email, password, full_name, role, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (str(uuid.uuid4()), username, email, hash_password(password), full_name, role, datetime.now().isoformat())
            )
    
    conn.commit()
    conn.close()

# Asegurar usuarios por defecto (solo cuando se usa SQLite)
if not os.getenv("DATABASE_URL", "").startswith("postgres"):
    ensure_default_users()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado"
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = decode_token(token)
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado"
        )
    
    return row_to_dict(user)

@app.post("/api/users/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate):
    conn = get_connection()
    cursor = conn.cursor()
    
    # Verificar username
    cursor.execute("SELECT id FROM users WHERE username = %s", (user.username,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre de usuario ya existe"
        )
    
    # Verificar email
    cursor.execute("SELECT id FROM users WHERE email = %s", (user.email,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo electrónico ya está registrado"
        )
    
    hashed_password = hash_password(user.password)
    user_id = str(uuid.uuid4())
    created_at = datetime.now().isoformat()
    
    cursor.execute(
        "INSERT INTO users (id, username, email, password, full_name, role, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (user_id, user.username, user.email, hashed_password, user.full_name, user.role, created_at)
    )
    conn.commit()
    
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    new_user = row_to_dict(cursor.fetchone())
    conn.close()
    
    del new_user['password']
    return new_user

@app.post("/api/users/login", response_model=TokenResponse)
def login(user_login: UserLogin):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = %s", (user_login.username,))
    user_row = cursor.fetchone()
    conn.close()
    
    if not user_row:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas"
        )
    
    user = row_to_dict(user_row)
    
    if not verify_password(user_login.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas"
        )
    
    # Convertir created_at a string si es datetime
    if isinstance(user.get("created_at"), datetime):
        user["created_at"] = user["created_at"].isoformat()
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["id"], "username": user["username"], "role": user["role"]},
        expires_delta=access_token_expires
    )
    
    del user['password']
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@app.get("/api/users/me", response_model=UserResponse)
def get_current_user_info(current_user: dict = Depends(get_current_user)):
    user_response = {k: v for k, v in current_user.items() if k != "password"}
    return user_response

@app.put("/api/users/me", response_model=UserResponse)
def update_current_user(user_update: UserUpdate, current_user: dict = Depends(get_current_user)):
    conn = get_connection()
    cursor = conn.cursor()
    
    if user_update.email:
        cursor.execute("SELECT id FROM users WHERE email = %s AND id != %s", (user_update.email, current_user["id"]))
        if cursor.fetchone():
            conn.close()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El correo electrónico ya está en uso"
            )
        cursor.execute("UPDATE users SET email = %s WHERE id = %s", (user_update.email, current_user["id"]))
    
    if user_update.full_name:
        cursor.execute("UPDATE users SET full_name = %s WHERE id = %s", (user_update.full_name, current_user["id"]))
    
    if user_update.password:
        hashed = hash_password(user_update.password)
        cursor.execute("UPDATE users SET password = %s WHERE id = %s", (hashed, current_user["id"]))
    
    conn.commit()
    
    cursor.execute("SELECT * FROM users WHERE id = %s", (current_user["id"],))
    updated_user = row_to_dict(cursor.fetchone())
    conn.close()
    
    del updated_user['password']
    return updated_user

@app.post("/api/users/verify-token")
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = decode_token(token)
    return {
        "valid": True, 
        "user_id": payload.get("sub"), 
        "username": payload.get("username"),
        "role": payload.get("role")
    }

@app.get("/")
def root():
    return {"service": "Users Service", "version": "1.0", "status": "running"}

@app.get("/health")
def health_check():
    """Health check endpoint para monitoreo"""
    try:
        # Verificar conexión a base de datos
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        conn.close()
        
        db_type = "PostgreSQL" if os.getenv("DATABASE_URL", "").startswith("postgres") else "SQLite"
        
        return {
            "status": "healthy",
            "service": "Users Service",
            "database": db_type,
            "database_connected": True
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "Users Service",
            "database_connected": False,
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8101))
    uvicorn.run(app, host="0.0.0.0", port=port)
