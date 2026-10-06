from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import hashlib
from app.database.db import get_db_connection

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

class RegisterSchema(BaseModel):
    full_name: str
    email: str
    password: str
    target_role: Optional[str] = "Software Engineer"

class LoginSchema(BaseModel):
    email: str
    password: str

def init_auth_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            target_role TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

init_auth_db()

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

@router.post("/register")
def register_user(payload: RegisterSchema):
    if not payload.email or not payload.password or not payload.full_name:
        raise HTTPException(status_code=400, detail="All fields are required")
    
    email_clean = payload.email.lower().strip()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email = ?", (email_clean,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="User with this email already exists")
    
    pwd_hash = hash_password(payload.password)
    cursor.execute(
        "INSERT INTO users (full_name, email, password_hash, target_role) VALUES (?, ?, ?, ?)",
        (payload.full_name.strip(), email_clean, pwd_hash, payload.target_role)
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
        
    return {
        "status": "success",
        "message": "Account created successfully!",
        "user": {
            "id": user_id,
            "full_name": payload.full_name,
            "email": payload.email,
            "target_role": payload.target_role
        }
    }

@router.post("/login")
def login_user(payload: LoginSchema):
    email_clean = payload.email.lower().strip()
    pwd_hash = hash_password(payload.password)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, full_name, email, target_role FROM users WHERE email = ? AND password_hash = ?",
        (email_clean, pwd_hash)
    )
    row = cursor.fetchone()
    conn.close()
        
    if not row:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    return {
        "status": "success",
        "message": "Logged in successfully!",
        "token": f"user_token_{row['id']}",
        "user": {
            "id": row['id'],
            "full_name": row['full_name'],
            "email": row['email'],
            "target_role": row['target_role']
        }
    }

@router.get("/me")
def get_current_user(email: str = "guest@example.com"):
    email_clean = email.lower().strip()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, full_name, email, target_role FROM users WHERE email = ?", (email_clean,))
    row = cursor.fetchone()
    conn.close()
        
    if row:
        return {
            "authenticated": True,
            "user": {"id": row['id'], "full_name": row['full_name'], "email": row['email'], "target_role": row['target_role']}
        }
    return {
        "authenticated": False,
        "user": {"full_name": "Guest Candidate", "email": "guest@example.com", "target_role": "AI Job Seeker"}
    }
