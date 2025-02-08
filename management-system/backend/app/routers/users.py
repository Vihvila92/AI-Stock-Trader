from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from app.database import get_management_db
from pydantic import BaseModel, EmailStr
from typing import Optional
import json

router = APIRouter(prefix="/users", tags=["Users"])

def log_event(db: Session, level: str, source: str, message: str, metadata: dict = None):
    """Log an event into the logs table in the database."""
    db.execute(text("""
        INSERT INTO logs (level, source, message, metadata)
        VALUES (:level, :source, :message, :metadata::json)
    """), {
        "level": level,
        "source": source,
        "message": message,
        "metadata": None if metadata is None else json.dumps(metadata)
    })
    db.commit()

class UserBase(BaseModel):
    username: str
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    role: str = "user"

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool

@router.get("/")
async def get_users(db: Session = Depends(get_management_db)):
    """Get all users."""
    log_event(db, "INFO", "user_management", "Listed all users")
    result = db.execute(text("""
        SELECT id, username, email, first_name, last_name, phone, role, is_active
        FROM users
    """))
    return [dict(row) for row in result]

@router.post("/", response_model=UserResponse)
async def create_user(user: UserCreate, db: Session = Depends(get_management_db)):
    """Create a new user."""
    try:
        # TODO: Add password hashing
        result = db.execute(text("""
            INSERT INTO users (username, email, first_name, last_name, phone, role, password_hash, is_active)
            VALUES (:username, :email, :first_name, :last_name, :phone, :role, :password, TRUE)
            RETURNING id, username, email, first_name, last_name, phone, role, is_active
        """), {**user.dict(), "password": user.password})
        db.commit()
        
        new_user = result.fetchone()
        log_event(
            db, "INFO", "user_management",
            f"Created new user",
            {"username": user.username, "email": user.email}
        )
        return dict(new_user)
    except Exception as e:
        log_event(
            db, "ERROR", "user_management",
            "Failed to create user",
            {"username": user.username, "error": str(e)}
        )
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{user_id}")
async def get_user(user_id: int, db: Session = Depends(get_management_db)):
    """Get user by ID."""
    result = db.execute(text("""
        SELECT id, username, email, first_name, last_name, phone, role, is_active
        FROM users WHERE id = :id
    """), {"id": user_id}).fetchone()
    
    if not result:
        log_event(
            db, "WARNING", "user_management",
            f"Attempted to fetch non-existent user",
            {"user_id": user_id}
        )
        raise HTTPException(status_code=404, detail="User not found")
    
    log_event(
        db, "INFO", "user_management",
        f"Retrieved user details",
        {"user_id": user_id}
    )
    return dict(result)

@router.delete("/{user_id}")
async def delete_user(user_id: int, db: Session = Depends(get_management_db)):
    """Delete user by ID."""
    result = db.execute(text("DELETE FROM users WHERE id = :id"), {"id": user_id})
    db.commit()
    
    if result.rowcount == 0:
        log_event(
            db, "WARNING", "user_management",
            f"Attempted to delete non-existent user",
            {"user_id": user_id}
        )
        raise HTTPException(status_code=404, detail="User not found")
    
    log_event(
        db, "INFO", "user_management",
        f"Deleted user",
        {"user_id": user_id}
    )
    return {"message": "User deleted"}
