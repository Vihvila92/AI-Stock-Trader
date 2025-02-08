from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from app.database import get_management_db
import json

router = APIRouter(prefix="/auth", tags=["Authentication"])

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

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/login")
async def login(request: LoginRequest, db: Session = Depends(get_management_db)):
    try:
        if request.username == "admin" and request.password == "password":
            log_event(
                db,
                level="INFO",
                source="authentication",
                message="Successful login",
                metadata={"username": request.username}
            )
            return {"message": "Login successful"}
        
        log_event(
            db,
            level="WARNING",
            source="authentication",
            message="Failed login attempt",
            metadata={"username": request.username}
        )
        raise HTTPException(status_code=401, detail="Invalid credentials")
    except Exception as e:
        log_event(
            db,
            level="ERROR",
            source="authentication",
            message="Login error",
            metadata={
                "username": request.username,
                "error": str(e)
            }
        )
        raise

@router.post("/logout")
async def logout(db: Session = Depends(get_management_db)):
    log_event(
        db,
        level="INFO",
        source="authentication",
        message="User logged out"
    )
    return {"message": "Logged out"}
