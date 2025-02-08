# Core imports
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from app.database import get_management_db  # Fixed import path
from pydantic import BaseModel
from typing import List, Optional
import json

router = APIRouter()

#================================================
# Data Models
#================================================

# Database-related models
class DatabaseBase(BaseModel):
    name: str
    type: str
    host: str
    port: int
    username: str
    password: str
    database_name: str
    connection_options: Optional[str] = None
    status: str = "active"

# System settings model
class SystemSetting(BaseModel):
    key: str
    value: str
    description: Optional[str] = None
    category: Optional[str] = None

# Authentication model
class AuthRequest(BaseModel):
    username: str
    password: str

#================================================
# Logging Function
#================================================

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

#================================================
# Database Management Endpoints
#================================================

@router.get("/databases", response_model=List[DatabaseBase])
def get_databases(db: Session = Depends(get_management_db)):
    log_event(db, "INFO", "database_management", "Listed all databases")
    result = db.execute(text("SELECT name, type, host, port, username, password, database_name, connection_options, status FROM databases"))
    return [dict(row) for row in result]

@router.post("/databases", response_model=DatabaseBase)
def create_database(database: DatabaseBase, db: Session = Depends(get_management_db)):
    try:
        db.execute(text("""
            INSERT INTO databases (name, type, host, port, username, password, database_name, connection_options, status)
            VALUES (:name, :type, :host, :port, :username, :password, :database_name, :connection_options, :status)
        """), database.dict())
        db.commit()
        log_event(
            db, "INFO", "database_management",
            f"Created new database connection: {database.name}",
            {"type": database.type, "host": database.host}
        )
        return database
    except Exception as e:
        log_event(
            db, "ERROR", "database_management",
            "Database creation failed",
            {"name": database.name, "error": str(e)}
        )
        raise

@router.delete("/databases/{database_name}")
def delete_database(database_name: str, db: Session = Depends(get_management_db)):
    log_event(
        db, "INFO", "database_management",
        f"Deleted database connection",
        {"name": database_name}
    )
    db.execute(text("DELETE FROM databases WHERE name = :database_name"), {"database_name": database_name})
    db.commit()
    return {"message": "Database deleted"}

#================================================
# System Settings Endpoints
#================================================

@router.get("/settings", response_model=List[SystemSetting])
def get_settings(db: Session = Depends(get_management_db)):
    log_event(db, "INFO", "system_settings", "Retrieved all settings")
    result = db.execute(text("""
        SELECT s.key, s.value, s.description, c.name AS category
        FROM system_settings s
        LEFT JOIN settings_categories c ON s.category_id = c.id
    """))
    return [dict(row) for row in result]

@router.post("/settings", response_model=SystemSetting)
def update_setting(setting: SystemSetting, db: Session = Depends(get_management_db)):
    try:
        db.execute(text("""
            UPDATE system_settings SET value = :value WHERE key = :key
        """), {"key": setting.key, "value": setting.value})
        db.commit()
        log_event(
            db, "INFO", "system_settings",
            f"Updated system setting",
            {"key": setting.key, "value": setting.value}
        )
        return setting
    except Exception as e:
        log_event(
            db, "ERROR", "system_settings",
            "Setting update failed",
            {"key": setting.key, "error": str(e)}
        )
        raise

#================================================
# Authentication Endpoints
#================================================

@router.post("/auth")
def authenticate_user(auth: AuthRequest, db: Session = Depends(get_management_db)):
    try:
        result = db.execute(text("SELECT id, username, password_hash FROM users WHERE username = :username"), 
                          {"username": auth.username}).fetchone()
        if not result:
            log_event(
                db, "WARNING", "authentication",
                "Failed login attempt - user not found",
                {"username": auth.username}
            )
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # TODO: Verify password hash (bcrypt)
        if auth.password != result.password_hash:
            log_event(
                db, "WARNING", "authentication",
                "Failed login attempt - invalid password",
                {"username": auth.username}
            )
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        log_event(
            db, "INFO", "authentication",
            "Successful login",
            {"username": auth.username, "user_id": result.id}
        )
        return {"message": "Authentication successful", "user_id": result.id}
    except Exception as e:
        if not isinstance(e, HTTPException):
            log_event(
                db, "ERROR", "authentication",
                "Authentication error",
                {"username": auth.username, "error": str(e)}
            )
        raise

#================================================
# Database Maintenance Endpoints
#================================================

@router.post("/init")
def initialize_database(db: Session = Depends(get_management_db)):
    """Initialize the management database (e.g., create initial tables)."""
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS example_table (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """))
    db.commit()
    return {"message": "Database initialized"}

@router.get("/check_updates")
def check_pending_updates(db: Session = Depends(get_management_db)):
    """Check if the management database schema needs updates."""
    # Logic to compare current schema version with the latest version
    result = db.execute(text("SELECT version FROM database_migrations ORDER BY id DESC LIMIT 1"))
    current_version = result.fetchone()
    latest_version = 2  # Replace with dynamic logic
    if current_version and current_version[0] < latest_version:
        return {"updates_needed": True, "current_version": current_version[0], "latest_version": latest_version}
    return {"updates_needed": False}

@router.post("/apply_updates")
def apply_updates(db: Session = Depends(get_management_db)):
    """Apply schema updates to the management database."""
    # Logic to run schema migrations (example below)
    db.execute(text("""
        ALTER TABLE example_table ADD COLUMN description TEXT;
    """))
    db.commit()
    return {"message": "Updates applied"}
