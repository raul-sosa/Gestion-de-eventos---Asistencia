from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timedelta
import json
import os
import uuid
import jwt
import bcrypt

app = FastAPI(title="Users Service - Sistema de Asistencias")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480

DB_FILE = "users_db.json"

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
    email: str
    full_name: str
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

def load_database():
    if not os.path.exists(DB_FILE):
        initial_data = {
            "users": []
        }
        # Admin
        initial_data["users"].append({
            "id": str(uuid.uuid4()),
            "username": "admin",
            "email": "admin@eventos.com",
            "password": hash_password("admin123"),
            "full_name": "Administrador",
            "role": "admin",
            "created_at": datetime.now().isoformat()
        })
        # Encargado
        initial_data["users"].append({
            "id": str(uuid.uuid4()),
            "username": "encargado",
            "email": "encargado@eventos.com",
            "password": hash_password("encargado123"),
            "full_name": "Encargado de Asistencia",
            "role": "encargado",
            "created_at": datetime.now().isoformat()
        })
        # Estudiante
        initial_data["users"].append({
            "id": str(uuid.uuid4()),
            "username": "estudiante",
            "email": "estudiante@eventos.com",
            "password": hash_password("estudiante123"),
            "full_name": "Estudiante Prueba",
            "role": "estudiante",
            "matricula": "12345",
            "created_at": datetime.now().isoformat()
        })
        save_database(initial_data)
        return initial_data
    
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_database(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
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
    
    db = load_database()
    user = next((u for u in db["users"] if u["id"] == user_id), None)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado"
        )
    
    return user

@app.post("/api/users/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate):
    db = load_database()
    
    if any(u["username"] == user.username for u in db["users"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre de usuario ya existe"
        )
    
    if any(u["email"] == user.email for u in db["users"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo electrónico ya está registrado"
        )
    
    hashed_password = hash_password(user.password)
    
    new_user = {
        "id": str(uuid.uuid4()),
        "username": user.username,
        "email": user.email,
        "password": hashed_password,
        "full_name": user.full_name,
        "role": user.role,
        "created_at": datetime.now().isoformat()
    }
    
    db["users"].append(new_user)
    save_database(db)
    
    user_response = {k: v for k, v in new_user.items() if k != "password"}
    return user_response

@app.post("/api/users/login", response_model=TokenResponse)
def login(user_login: UserLogin):
    db = load_database()
    
    user = next((u for u in db["users"] if u["username"] == user_login.username), None)
    
    if not user or not verify_password(user_login.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas"
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["id"], "username": user["username"], "role": user["role"]},
        expires_delta=access_token_expires
    )
    
    user_response = {k: v for k, v in user.items() if k != "password"}
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user_response
    }

@app.get("/api/users/me", response_model=UserResponse)
def get_current_user_info(current_user: dict = Depends(get_current_user)):
    user_response = {k: v for k, v in current_user.items() if k != "password"}
    return user_response

@app.put("/api/users/me", response_model=UserResponse)
def update_current_user(user_update: UserUpdate, current_user: dict = Depends(get_current_user)):
    db = load_database()
    
    user_index = next((i for i, u in enumerate(db["users"]) if u["id"] == current_user["id"]), None)
    
    if user_index is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    if user_update.email:
        if any(u["email"] == user_update.email and u["id"] != current_user["id"] for u in db["users"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El correo electrónico ya está en uso"
            )
        db["users"][user_index]["email"] = user_update.email
    
    if user_update.full_name:
        db["users"][user_index]["full_name"] = user_update.full_name
    
    if user_update.password:
        db["users"][user_index]["password"] = hash_password(user_update.password)
    
    save_database(db)
    
    updated_user = db["users"][user_index]
    user_response = {k: v for k, v in updated_user.items() if k != "password"}
    return user_response

@app.post("/api/users/verify-token")
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = decode_token(token)
    return {"valid": True, "user_id": payload.get("sub"), "username": payload.get("username")}

@app.get("/")
def root():
    return {"service": "Users Service", "version": "1.0", "status": "running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8101)
